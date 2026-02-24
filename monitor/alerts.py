from __future__ import annotations

from dataclasses import dataclass

from asgiref.sync import async_to_sync
from django.db import transaction
from django.utils import timezone

from .models import AlertEvent, AlertRule, AlertState, Server
from .services.notification_service import NotificationService

# Initialize notification service
notification_service = NotificationService()

@dataclass
class AlertEvalResult:
    fired_event: AlertEvent | None
    recovered_event: AlertEvent | None


def _parse_tags(s: str) -> set[str]:
    s = (s or "").strip().lower()
    if not s:
        return set()
    raw = s.replace(";", ",").replace("|", ",")
    parts = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts.extend([p.strip() for p in chunk.split() if p.strip()])
    return set(parts)


def _matches_rule_scope(rule: AlertRule, server: Server) -> bool:
    if rule.pinned_only and not server.pinned:
        return False

    wanted = _parse_tags(rule.tags_filter)
    if not wanted:
        return True

    # If server is a NetworkDevice, it doesn't have tags field in the same way, 
    # but we'll check if name matches or just allow if no filter
    if hasattr(server, 'tags'):
        have = _parse_tags(server.tags)
        if not have:
            return False
        return bool(wanted.intersection(have))
    
    return True


def _rule_condition(rule: AlertRule, server: Server, now):
    k = rule.kind

    if k == AlertRule.KIND_SERVER_DOWN:
        return server.last_status == "DOWN", None

    if k == AlertRule.KIND_DEVICE_DOWN:
        # Check for NetworkDevice status
        if hasattr(server, 'last_status'):
            return server.last_status == "DOWN", None
        return False, None

    if k == AlertRule.KIND_HTTP_UNHEALTHY:
        if hasattr(server, 'http_check'):
            return server.http_check and server.last_http_ok is False, None
        return False, None

    if k == AlertRule.KIND_AGENT_STALE:
        if not hasattr(server, 'last_resource_checked'):
            return False, None
        last = server.last_resource_checked
        if last is None:
            return True, None
        age = (now - last).total_seconds()
        threshold = float(rule.threshold) if rule.threshold is not None else float(rule.duration_seconds or 0)
        if threshold <= 0:
            threshold = 120.0
        return age > threshold, age

    if k == AlertRule.KIND_DB_CONNECT_FAIL:
        if hasattr(server, 'last_db_connect_ok'):
            return server.last_db_connect_ok is False, None
        return False, None

    if k == AlertRule.KIND_CPU_HIGH:
        if rule.threshold is None or not hasattr(server, 'last_cpu_percent'):
            return False, None
        if server.last_cpu_percent is None:
            return False, None
        return float(server.last_cpu_percent) >= float(rule.threshold), float(server.last_cpu_percent)

    if k == AlertRule.KIND_RAM_HIGH:
        if rule.threshold is None or not hasattr(server, 'last_ram_percent'):
            return False, None
        if server.last_ram_percent is None:
            return False, None
        return float(server.last_ram_percent) >= float(rule.threshold), float(server.last_ram_percent)

    if k == AlertRule.KIND_DB_CONN_HIGH:
        if rule.threshold is None or not hasattr(server, 'last_db_conn_usage_percent'):
            return False, None
        if server.last_db_conn_usage_percent is None:
            return False, None
        return float(server.last_db_conn_usage_percent) >= float(rule.threshold), float(server.last_db_conn_usage_percent)

    return False, None


def _event_payload(e: AlertEvent) -> dict:
    from .models import Server, NetworkDevice
    
    server_data = {"id": None, "name": "Unknown"}
    if e.server_id:
        # Check if it's a Server or NetworkDevice for naming
        try:
            srv = Server.objects.get(id=e.server_id)
            server_data = {"id": srv.id, "name": srv.name, "type": "server"}
        except Server.DoesNotExist:
            try:
                # We reuse server_id field for NetworkDevice id in AlertEvent for now 
                # or we might need a separate field. Given the current schema:
                # server = models.ForeignKey(Server, ...)
                # If NetworkDevice is not a Server, this might fail if not nullable.
                # Let's check models.py for AlertEvent.
                pass
            except:
                pass

    return {
        "id": e.id,
        "created_at": e.created_at.isoformat() if e.created_at else None,
        "server": server_data,
        "rule_id": e.rule_id,
        "kind": e.kind,
        "severity": e.severity,
        "is_recovery": e.is_recovery,
        "title": e.title,
        "message": e.message,
        "value": e.value,
        "payload": e.payload,
    }


def _evaluate_rule(rule: AlertRule, server: Server, now: datetime, channel_layer=None) -> tuple[list[dict], bool]:
    if not _matches_rule_scope(rule, server):
        return [], False

    cond, value = _rule_condition(rule, server, now)
    emitted = []
    is_active = False
    
    # Identify if it's a Server or NetworkDevice for the AlertState
    from .models import Server, NetworkDevice, AlertState
    
    # NOTE: AlertState currently has a ForeignKey to Server. 
    # If we want to monitor NetworkDevice, we need to handle this.
    # For now, let's assume we only evaluate Server rules here to avoid DB errors.
    if not isinstance(server, Server):
        # Handle NetworkDevice alerts differently or skip for now if schema doesn't support it
        return [], False

    with transaction.atomic():
        state, _ = AlertState.objects.select_for_update().get_or_create(rule=rule, server=server)
        state.last_seen_at = now

        fired_evt = None
        recovered_evt = None

        if cond:
            if state.is_active:
                state.save(update_fields=["last_seen_at"])
                is_active = True
            else:
                if state.pending_since is None:
                    state.pending_since = now
                    state.save(update_fields=["pending_since", "last_seen_at"])
                else:
                    dur = int(rule.duration_seconds or 0)
                    if dur <= 0 or (now - state.pending_since).total_seconds() >= dur:
                        state.is_active = True
                        state.active_since = now
                        state.save(
                            update_fields=[
                                "is_active",
                                "active_since",
                                "last_seen_at",
                            ]
                        )
                        is_active = True
                        
                        # Build detailed message with resource status
                        msg = rule.kind
                        if hasattr(server, 'last_cpu_percent') and server.last_cpu_percent is not None:
                            msg += f" (CPU: {server.last_cpu_percent}%, RAM: {server.last_ram_percent}%, Disk: {server.last_disk_percent}%)"

                        fired_evt = AlertEvent.objects.create(
                            server=server,
                            rule=rule,
                            kind=rule.kind,
                            severity=rule.severity,
                            is_recovery=False,
                            title=rule.name,
                            message=msg,
                            value=value,
                            payload={"kind": rule.kind, "value": value},
                        )
        else:
            if state.is_active:
                state.is_active = False
                state.pending_since = None
                state.active_since = None
                state.save(
                    update_fields=[
                        "is_active",
                        "pending_since",
                        "active_since",
                        "last_seen_at",
                    ]
                )
                recovered_evt = AlertEvent.objects.create(
                    server=server,
                    rule=rule,
                    kind=rule.kind,
                    severity=rule.severity,
                    is_recovery=True,
                    title=rule.name,
                    message=rule.kind,
                    value=value,
                    payload={"kind": rule.kind, "value": value},
                )
            else:
                state.pending_since = None
                state.save(update_fields=["pending_since", "last_seen_at"])

    if fired_evt is not None:
        payload = _event_payload(fired_evt)
        emitted.append(payload)
        if channel_layer is not None:
            async_to_sync(channel_layer.group_send)(
                "status",
                {"type": "alert.event", "event": payload},
            )
        
        # Send notification
        channels = list(rule.notification_channels) if rule.notification_channels else ['console']
        if 'push' not in channels:
            channels.append('push')
            
        subject = f"ALERT: {fired_evt.title} on {server.name}"
        
        # Include resource status in notification message
        resource_info = ""
        if hasattr(server, 'last_cpu_percent') and server.last_cpu_percent is not None:
            resource_info = f"\nStatus: CPU {server.last_cpu_percent}%, RAM {server.last_ram_percent}%, Disk {server.last_disk_percent}%"
            
        message = f"Severity: {fired_evt.severity}\nMessage: {fired_evt.message}\nValue: {fired_evt.value}{resource_info}"
        notification_service.send_notification(channels, "admin", subject, message)

    if recovered_evt is not None:
        payload = _event_payload(recovered_evt)
        emitted.append(payload)
        if channel_layer is not None:
            async_to_sync(channel_layer.group_send)(
                "status",
                {"type": "alert.event", "event": payload},
            )
        
        # Send notification
        channels = list(rule.notification_channels) if rule.notification_channels else ['console']
        if 'push' not in channels:
            channels.append('push')
            
        subject = f"RECOVERY: {recovered_evt.title} on {server.name}"
        message = f"Severity: {recovered_evt.severity}\nMessage: {recovered_evt.message}\nValue: {recovered_evt.value}"
        notification_service.send_notification(channels, "admin", subject, message)

    return emitted, is_active


def evaluate_alerts_for_device(device: NetworkDevice, now=None, channel_layer=None) -> list[dict]:
    """
    Evaluate alerts for a NetworkDevice.
    Note: Current schema AlertState/AlertEvent depends on Server model.
    If we want to support NetworkDevice alerts, we may need to adapt these models.
    For now, we implement a simplified check that logs to console or sends direct notifications.
    """
    if now is None:
        now = timezone.now()

    if not device.enabled:
        return []

    rules = list(AlertRule.objects.filter(enabled=True, kind=AlertRule.KIND_DEVICE_DOWN).order_by("id"))
    emitted = []
    
    for rule in rules:
        cond, _ = _rule_condition(rule, device, now)
        if cond:
            # Simple notification for now as AlertState doesn't support NetworkDevice yet
            logger.warning(f"DEVICE ALERT: {device.name} is DOWN!")
            
            # Send notification if not already sent recently (simple throttling could be added)
            channels = list(rule.notification_channels) if rule.notification_channels else ['console', 'push']
            subject = f"ALERT: {device.name} is DOWN"
            message = f"Network device {device.name} ({device.ip_address}) is not responding to ping."
            notification_service.send_notification(channels, "admin", subject, message)
            
    return emitted



def evaluate_alerts_for_server(server: Server, now=None, channel_layer=None) -> list[dict]:
    if now is None:
        now = timezone.now()

    if not server.enabled:
        return []

    rules = list(AlertRule.objects.filter(enabled=True).order_by("id"))
    emitted: list[dict] = []
    
    # Separation of rules
    server_down_rules = [r for r in rules if r.kind == AlertRule.KIND_SERVER_DOWN]
    other_rules = [r for r in rules if r.kind != AlertRule.KIND_SERVER_DOWN]
    
    is_server_down = False

    # 1. Evaluate Server Down rules first
    for rule in server_down_rules:
        payloads, active = _evaluate_rule(rule, server, now, channel_layer)
        emitted.extend(payloads)
        if active:
            is_server_down = True
            
    # 2. Evaluate other rules ONLY if server is NOT down
    if not is_server_down:
        for rule in other_rules:
            payloads, _ = _evaluate_rule(rule, server, now, channel_layer)
            emitted.extend(payloads)

    return emitted
