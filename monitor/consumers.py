from __future__ import annotations

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .models import Server, AlertEvent


class StatusConsumer(AsyncJsonWebsocketConsumer):
    group_name = "status"

    async def connect(self):
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_snapshot()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_snapshot(self):
        servers = await self._get_servers_payload()
        await self.send_json({"type": "snapshot", "servers": servers})

    async def server_status(self, event):
        await self.send_json({"type": "update", "server": event.get("server")})

    async def server_metrics(self, event):
        await self.send_json({"type": "metrics_update", "server": event.get("server")})

    @database_sync_to_async
    def _get_servers_payload(self):
        servers = []
        for server in Server.objects.all().order_by("-pinned", "name"):
            servers.append({
                "id": server.id,
                "name": server.name,
                "pinned": server.pinned,
                "tags": server.tags,
                "server_type": server.server_type,
                "server_type_display": server.get_server_type_display(),
                "ip_address": str(server.ip_address),
                "port": server.port,
                "last_status": server.last_status,
                "last_status_display": server.get_last_status_display(),
                "last_http_ok": server.last_http_ok,
                "last_latency_ms": server.last_latency_ms,
                "last_http_status_code": server.last_http_status_code,
                "last_checked": server.last_checked.isoformat() if server.last_checked else None,
                "last_error": server.last_error,
                "last_resource_checked": server.last_resource_checked.isoformat() if server.last_resource_checked else None,
                "last_cpu_percent": server.last_cpu_percent,
                "last_ram_percent": server.last_ram_percent,
                "last_load_1": server.last_load_1,
                "last_uptime_seconds": server.last_uptime_seconds,
                "last_boot_time": server.last_boot_time.isoformat() if server.last_boot_time else None,
                "last_db_checked": server.last_db_checked.isoformat() if server.last_db_checked else None,
                "last_db_process_up": server.last_db_process_up,
                "last_db_port_ok": server.last_db_port_ok,
                "last_db_connect_ok": server.last_db_connect_ok,
                "last_db_ping_ms": server.last_db_ping_ms,
                "last_db_connections": server.last_db_connections,
                "last_db_max_connections": server.last_db_max_connections,
                "last_db_conn_usage_percent": server.last_db_conn_usage_percent,
                "last_db_qps": server.last_db_qps,
                "last_db_read_qps": server.last_db_read_qps,
                "last_db_write_qps": server.last_db_write_qps,
                "last_db_tps": server.last_db_tps,
                "last_db_avg_query_ms": server.last_db_avg_query_ms,
                "last_db_p95_query_ms": server.last_db_p95_query_ms,
                "last_db_p99_query_ms": server.last_db_p99_query_ms,
                "last_db_slow_1m": server.last_db_slow_1m,
                "enabled": server.enabled,
            })
        return servers


class MonitoringConsumer(AsyncJsonWebsocketConsumer):
    group_name = "monitoring"

    async def connect(self):
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_initial_data()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_initial_data(self):
        servers = await self._get_servers_payload()
        events = await self._get_recent_events()
        await self.send_json({
            "type": "initial_data",
            "servers": servers,
            "events": events
        })

    async def server_update(self, event):
        await self.send_json({"type": "server_update", "server": event.get("server")})

    @database_sync_to_async
    def _get_servers_payload(self):
        from .services.metrics_monitor_service import MetricsMonitorService
        from .models_metrics import ServerMetrics
        monitor = MetricsMonitorService()
        
        servers = []
        for server in Server.objects.all().order_by("-pinned", "name"):
            # Get latest agent metrics for SSL summary
            latest_metrics = ServerMetrics.objects.filter(server=server).order_by('-timestamp').first()
            ssl_summary = None
            if latest_metrics:
                formatted = monitor.format_agent_metrics(latest_metrics, server)
                ssl_summary = formatted.get('ssl_summary')

            servers.append({
                "id": server.id,
                "name": server.name,
                "pinned": server.pinned,
                "tags": server.tags,
                "server_type": server.server_type,
                "server_type_display": server.get_server_type_display(),
                "ip_address": str(server.ip_address),
                "port": server.port,
                "last_status": server.last_status,
                "last_status_display": server.get_last_status_display(),
                "last_http_ok": server.last_http_ok,
                "last_latency_ms": server.last_latency_ms,
                "last_http_status_code": server.last_http_status_code,
                "last_checked": server.last_checked.isoformat() if server.last_checked else None,
                "last_error": server.last_error,
                "last_resource_checked": server.last_resource_checked.isoformat() if server.last_resource_checked else None,
                "last_cpu_percent": server.last_cpu_percent,
                "last_ram_percent": server.last_ram_percent,
                "last_load_1": server.last_load_1,
                "last_uptime_seconds": server.last_uptime_seconds,
                "last_boot_time": server.last_boot_time.isoformat() if server.last_boot_time else None,
                "last_db_checked": server.last_db_checked.isoformat() if server.last_db_checked else None,
                "last_db_process_up": server.last_db_process_up,
                "last_db_port_ok": server.last_db_port_ok,
                "last_db_connect_ok": server.last_db_connect_ok,
                "last_db_ping_ms": server.last_db_ping_ms,
                "last_db_connections": server.last_db_connections,
                "last_db_max_connections": server.last_db_max_connections,
                "last_db_conn_usage_percent": server.last_db_conn_usage_percent,
                "last_db_qps": server.last_db_qps,
                "last_db_read_qps": server.last_db_read_qps,
                "last_db_write_qps": server.last_db_write_qps,
                "last_db_tps": server.last_db_tps,
                "last_db_avg_query_ms": server.last_db_avg_query_ms,
                "last_db_p95_query_ms": server.last_db_p95_query_ms,
                "last_db_p99_query_ms": server.last_db_p99_query_ms,
                "last_db_slow_1m": server.last_db_slow_1m,
                "enabled": server.enabled,
                "ssl_summary": ssl_summary,
            })
        return servers

    @database_sync_to_async
    def _get_recent_events(self):
        events = []
        for event in AlertEvent.objects.select_related('server', 'rule').order_by("-created_at")[:20]:
            events.append({
                "id": event.id,
                "server_name": event.server.name,
                "title": event.title,
                "severity": event.severity,
                "created_at": event.created_at.isoformat(),
                "is_recovery": event.is_recovery,
            })
        return events
