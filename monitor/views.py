from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

from django.db import transaction
import math
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
import csv
from io import StringIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .alerts import evaluate_alerts_for_server
from .forms import ServerForm, ISPConnectionForm
from .models import (
    AlertEvent,
    CheckResult,
    CCTVDevice,
    DbSample,
    DiskIOSample,
    DiskUsageSample,
    NetworkSample,
    RebootEvent,
    ResourceSample,
    Server,
    NetworkDevice,
    NetworkInterface,
    NetworkMetric,
    SecurityEvent,
    TrafficLog,
    ISPConnection,
    ISPMetric,
    ISPFailover,
    DeviceBandwidthMeasurement,
)
from .services.bandwidth_reports import BandwidthReportService
from .services.network_scanner import NetworkScanner
from .services.bandwidth_monitor import BandwidthMonitor
from .services.firewall_interface_monitor import FirewallInterfaceMonitor
from monitor.services.ssl_cache_service import get_cached_ssl_certificates


@login_required
def infra_wiki(request):
    """
    Renders the ISCE Infrastructure Wiki page.
    """
    return render(request, 'monitor/isce-infra-wiki.html')


def _parse_range_param(range_param: str):
    range_param = (range_param or "30").strip().lower()
    max_points = 2000

    limit = None
    since = None

    if range_param == "all":
        limit = max_points
    elif range_param.endswith("h"):
        try:
            hours = int(range_param[:-1])
            since = timezone.now() - timedelta(hours=hours)
        except ValueError:
            limit = 30
    elif range_param.endswith("d"):
        try:
            days = int(range_param[:-1])
            since = timezone.now() - timedelta(days=days)
        except ValueError:
            limit = 30
    else:
        try:
            limit = int(range_param)
        except ValueError:
            limit = 30

    if limit is None:
        limit = 30

    limit = max(1, min(limit, max_points))
    return range_param, since, limit, max_points


def _parse_collected_at(payload: dict) -> datetime:
    raw = payload.get("collected_at") or payload.get("ts") or payload.get("timestamp")
    if not raw:
        return timezone.now()

    dt = parse_datetime(str(raw))
    if dt is None:
        return timezone.now()
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def _bearer_token(request) -> str | None:
    auth = request.headers.get("Authorization") or request.META.get("HTTP_AUTHORIZATION")
    if not auth:
        return None
    parts = auth.split(" ", 1)
    if len(parts) != 2:
        return None
    scheme, token = parts[0].strip().lower(), parts[1].strip()
    if scheme != "bearer" or not token:
        return None
    return token


def dashboard(request):
    from django.core.cache import cache
    
    # Try to get grouped servers from cache
    cache_key = "dashboard_grouped_servers"
    cached_data = cache.get(cache_key)
    
    if cached_data and not request.GET.get('refresh'):
        servers_by_type = cached_data['servers_by_type']
        servers = cached_data['servers']
    else:
        # Optimize with select_related and prefetch_related
        servers = list(Server.objects.all()
                      .select_related('ssh_credential')
                      .order_by("server_type", "-pinned", "name"))
        
        # Sort by IP address numerically within each type group
        def extract_ip_numeric(ip_str):
            try:
                parts = ip_str.split('.')
                return tuple(int(part) for part in parts)
            except (ValueError, AttributeError):
                return (0, 0, 0, 0)
        
        servers.sort(key=lambda x: (
            x.server_type,
            extract_ip_numeric(x.ip_address) if x.ip_address else (0, 0, 0, 0),
            not x.pinned,
            x.name.lower()
        ))
        
        # Group servers by type
        servers_by_type = {}
        for server in servers:
            server_type = server.get_server_type_display()
            if server_type not in servers_by_type:
                servers_by_type[server_type] = []
            servers_by_type[server_type].append(server)
            
        # Cache for 1 minute
        cache.set(cache_key, {'servers_by_type': servers_by_type, 'servers': servers}, 60)
    
    # Load SSH metrics from cache ONLY (Do not initiate network checks in view)
    server_metrics = {}
    try:
        from django.core.cache import cache
        cache_key = "dashboard_metrics"
        server_metrics = cache.get(cache_key, {})
    except Exception as e:
        logger.error(f"Error in dashboard metrics cache loading: {e}")
    
    # Add metrics to server objects
    for server in servers:
        server.ssh_metrics = server_metrics.get(server.id, {})
    
    # Get SSL certificate information - WITH CACHING
    try:
        ssl_certificates, ssl_summary = get_cached_ssl_certificates()
        logger.info(f"SSL certificates loaded from cache for {len(ssl_certificates)} devices")
    except Exception as e:
        logger.error(f"Error loading SSL certificates from cache: {e}")
        # Fallback to empty data
        ssl_certificates = {}
        ssl_summary = {
            'total': 0,
            'good': 0,
            'warning': 0,
            'critical': 0,
            'expired': 0,
            'error': 0
        }

    return render(request, "monitor/dashboard_new.html", {
        "servers": servers,
        "servers_by_type": servers_by_type,
        "ssl_certificates": ssl_certificates,
        "ssl_summary": ssl_summary,
        "active_nav": "dashboard",
    })


@login_required
def ssl_certificates_list(request):
    """View to list all monitored SSL certificates"""
    from .models import SSLCertificate
    certificates = SSLCertificate.objects.filter(enabled=True).select_related('server').order_by('expires_at')
    
    return render(request, 'monitor/ssl_certificates_list.html', {
        'certificates': certificates,
        'active_nav': 'ssl'
    })


@require_GET
def status_api(request):
    servers = Server.objects.filter(enabled=True).order_by("-pinned", "name")
    payload = [
        {
            "id": s.id,
            "name": s.name,
            "pinned": s.pinned,
            "tags": s.tags,
            "server_type": s.server_type,
            "server_type_display": s.get_server_type_display(),
            "ip_address": s.ip_address,
            "port": s.port,
            "last_status": s.last_status,
            "last_status_display": s.get_last_status_display(),
            "last_http_ok": s.last_http_ok,
            "last_latency_ms": s.last_latency_ms,
            "last_http_status_code": s.last_http_status_code,
            "last_checked": s.last_checked.isoformat() if s.last_checked else None,
            "last_error": s.last_error,
            "last_resource_checked": s.last_resource_checked.isoformat() if s.last_resource_checked else None,
            "last_cpu_percent": s.last_cpu_percent,
            "last_ram_percent": s.last_ram_percent,
            "last_load_1": s.last_load_1,
            "last_uptime_seconds": s.last_uptime_seconds,
            "last_boot_time": s.last_boot_time.isoformat() if s.last_boot_time else None,
            "last_db_checked": s.last_db_checked.isoformat() if s.last_db_checked else None,
            "last_db_process_up": s.last_db_process_up,
            "last_db_port_ok": s.last_db_port_ok,
            "last_db_connect_ok": s.last_db_connect_ok,
            "last_db_ping_ms": s.last_db_ping_ms,
            "last_db_connections": s.last_db_connections,
            "last_db_max_connections": s.last_db_max_connections,
            "last_db_conn_usage_percent": s.last_db_conn_usage_percent,
            "last_db_qps": s.last_db_qps,
            "last_db_read_qps": s.last_db_read_qps,
            "last_db_write_qps": s.last_db_write_qps,
            "last_db_tps": s.last_db_tps,
            "last_db_avg_query_ms": s.last_db_avg_query_ms,
            "last_db_p95_query_ms": s.last_db_p95_query_ms,
            "last_db_p99_query_ms": s.last_db_p99_query_ms,
            "last_db_slow_1m": s.last_db_slow_1m,
        }
        for s in servers
    ]
    return JsonResponse({"servers": payload})


@require_GET
def history_api(request):
    try:
        limit = int(request.GET.get("limit", "30"))
    except ValueError:
        limit = 30
    limit = max(1, min(limit, 200))

    server_ids = list(Server.objects.filter(enabled=True).values_list("id", flat=True))
    remaining = {sid: limit for sid in server_ids}
    history: dict[str, list[dict]] = {str(sid): [] for sid in server_ids}

    qs = (
        CheckResult.objects.filter(server_id__in=server_ids)
        .select_related("server")
        .order_by("-checked_at")
    )

    for cr in qs.iterator():
        if not remaining:
            break

        sid = cr.server_id
        need = remaining.get(sid)
        if need is None:
            continue

        history[str(sid)].append(
            {
                "checked_at": cr.checked_at.isoformat() if cr.checked_at else None,
                "status": cr.status,
                "http_ok": cr.http_ok,
                "latency_ms": cr.latency_ms,
                "http_status_code": cr.http_status_code,
            }
        )

        need -= 1
        if need <= 0:
            remaining.pop(sid, None)
        else:
            remaining[sid] = need

    for sid, points in history.items():
        points.reverse()

    return JsonResponse({"limit": limit, "history": history})


@require_GET
def resource_history_api(request):
    try:
        limit = int(request.GET.get("limit", "30"))
    except ValueError:
        limit = 30
    limit = max(1, min(limit, 200))

    server_ids = list(Server.objects.filter(enabled=True).values_list("id", flat=True))
    remaining = {sid: limit for sid in server_ids}
    history: dict[str, list[dict]] = {str(sid): [] for sid in server_ids}

    qs = ResourceSample.objects.filter(server_id__in=server_ids).order_by("-collected_at")

    for rs in qs.iterator():
        if not remaining:
            break

        sid = rs.server_id
        need = remaining.get(sid)
        if need is None:
            continue

        history[str(sid)].append(
            {
                "collected_at": rs.collected_at.isoformat() if rs.collected_at else None,
                "cpu_percent": rs.cpu_percent,
                "ram_percent": rs.ram_percent,
                "load_1": rs.load_1,
            }
        )

        need -= 1
        if need <= 0:
            remaining.pop(sid, None)
        else:
            remaining[sid] = need

    for sid, points in history.items():
        points.reverse()

    return JsonResponse({"limit": limit, "history": history})


@csrf_exempt
@require_http_methods(["POST"])
def agent_ingest_api(request):
    token = _bearer_token(request)
    if not token:
        return JsonResponse({"error": "missing_bearer_token"}, status=401)

    server = Server.objects.filter(agent_token=token).first()
    if server is None:
        return JsonResponse({"error": "invalid_token"}, status=401)

    try:
        payload = json.loads((request.body or b"{}").decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid_json"}, status=400)

    if not isinstance(payload, dict):
        return JsonResponse({"error": "invalid_payload"}, status=400)

    collected_at = _parse_collected_at(payload)

    cpu = payload.get("cpu") or {}
    mem = payload.get("memory") or payload.get("mem") or {}
    load = payload.get("load") or {}
    uptime = payload.get("uptime") or {}

    cpu_percent = cpu.get("percent") if isinstance(cpu, dict) else payload.get("cpu_percent")
    ram_total = mem.get("total_bytes") if isinstance(mem, dict) else payload.get("ram_total_bytes")
    ram_used = mem.get("used_bytes") if isinstance(mem, dict) else payload.get("ram_used_bytes")
    ram_percent = mem.get("percent") if isinstance(mem, dict) else payload.get("ram_percent")

    load_1 = load.get("1") if isinstance(load, dict) else payload.get("load_1")
    load_5 = load.get("5") if isinstance(load, dict) else payload.get("load_5")
    load_15 = load.get("15") if isinstance(load, dict) else payload.get("load_15")

    # Validation
    try:
        def validate_num(v, name, min_v=None, max_v=None):
            if v is None: return None
            try:
                val = float(v)
            except (ValueError, TypeError):
                raise ValueError(f"{name} must be numeric")
            if min_v is not None and val < min_v:
                raise ValueError(f"{name} must be >= {min_v}")
            if max_v is not None and val > max_v:
                raise ValueError(f"{name} must be <= {max_v}")
            return val

        cpu_percent = validate_num(cpu_percent, "cpu_percent", 0, 110.0) # Allow slight overshoot
        ram_percent = validate_num(ram_percent, "ram_percent", 0, 100.0)
        
        if ram_total is not None:
             validate_num(ram_total, "ram_total", 0)

        load_1 = validate_num(load_1, "load_1", 0)
        load_5 = validate_num(load_5, "load_5", 0)
        load_15 = validate_num(load_15, "load_15", 0)
             
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)

    boot_time_raw = uptime.get("boot_time") if isinstance(uptime, dict) else payload.get("boot_time")
    boot_time = None
    if boot_time_raw is not None and boot_time_raw != "":
        boot_time = parse_datetime(str(boot_time_raw))
        if boot_time is None:
            try:
                boot_time = timezone.datetime.fromtimestamp(
                    float(boot_time_raw),
                    tz=timezone.get_current_timezone(),
                )
            except (TypeError, ValueError, OSError):
                boot_time = None
    if boot_time is not None and timezone.is_naive(boot_time):
        boot_time = timezone.make_aware(boot_time, timezone.get_current_timezone())

    uptime_seconds = uptime.get("uptime_seconds") if isinstance(uptime, dict) else payload.get("uptime_seconds")

    disk_io = payload.get("disk_io") or payload.get("diskio") or {}
    net = payload.get("network") or payload.get("net") or {}
    disks = payload.get("disks") or payload.get("disk_usage") or []
    db = payload.get("db") or {}

    with transaction.atomic():
        ResourceSample.objects.create(
            server=server,
            collected_at=collected_at,
            cpu_percent=cpu_percent,
            load_1=load_1,
            load_5=load_5,
            load_15=load_15,
            ram_total_bytes=ram_total,
            ram_used_bytes=ram_used,
            ram_percent=ram_percent,
            boot_time=boot_time,
            uptime_seconds=uptime_seconds,
        )

        if isinstance(disk_io, dict) and disk_io:
            DiskIOSample.objects.create(
                server=server,
                collected_at=collected_at,
                read_bytes=disk_io.get("read_bytes"),
                write_bytes=disk_io.get("write_bytes"),
                read_time_ms=disk_io.get("read_time_ms"),
                write_time_ms=disk_io.get("write_time_ms"),
            )

        if isinstance(net, dict) and net:
            NetworkSample.objects.create(
                server=server,
                collected_at=collected_at,
                bytes_sent=net.get("bytes_sent"),
                bytes_recv=net.get("bytes_recv"),
                packets_sent=net.get("packets_sent"),
                packets_recv=net.get("packets_recv"),
                errin=net.get("errin"),
                errout=net.get("errout"),
                dropin=net.get("dropin"),
                dropout=net.get("dropout"),
            )

        if isinstance(disks, list) and disks:
            for d in disks:
                if not isinstance(d, dict):
                    continue
                mount = d.get("mount") or d.get("path")
                if not mount:
                    continue
                DiskUsageSample.objects.create(
                    server=server,
                    collected_at=collected_at,
                    mount=str(mount),
                    fstype=str(d.get("fstype") or ""),
                    total_bytes=d.get("total_bytes"),
                    used_bytes=d.get("used_bytes"),
                    percent=d.get("percent"),
                )

        if isinstance(db, dict) and db:
            DbSample.objects.create(
                server=server,
                collected_at=collected_at,
                engine=str(db.get("engine") or ""),
                process_up=db.get("process_up"),
                port_ok=db.get("port_ok"),
                port_ms=db.get("port_ms"),
                connect_ok=db.get("connect_ok"),
                ping_ms=db.get("ping_ms"),
                current_connections=db.get("current_connections"),
                max_connections=db.get("max_connections"),
                connection_usage_percent=db.get("connection_usage_percent"),
                qps=db.get("qps"),
                read_qps=db.get("read_qps"),
                write_qps=db.get("write_qps"),
                tps=db.get("tps"),
                avg_query_ms=db.get("avg_query_ms"),
                p95_query_ms=db.get("p95_query_ms"),
                p99_query_ms=db.get("p99_query_ms"),
                slow_queries_1m=db.get("slow_queries_1m"),
            )

            server.last_db_checked = collected_at
            server.last_db_process_up = db.get("process_up")
            server.last_db_port_ok = db.get("port_ok")
            server.last_db_connect_ok = db.get("connect_ok")
            server.last_db_ping_ms = db.get("ping_ms")
            server.last_db_connections = db.get("current_connections")
            server.last_db_max_connections = db.get("max_connections")
            server.last_db_conn_usage_percent = db.get("connection_usage_percent")
            server.last_db_qps = db.get("qps")
            server.last_db_read_qps = db.get("read_qps")
            server.last_db_write_qps = db.get("write_qps")
            server.last_db_tps = db.get("tps")
            server.last_db_avg_query_ms = db.get("avg_query_ms")
            server.last_db_p95_query_ms = db.get("p95_query_ms")
            server.last_db_p99_query_ms = db.get("p99_query_ms")
            server.last_db_slow_1m = db.get("slow_queries_1m")

        if boot_time is not None and server.last_boot_time and server.last_boot_time != boot_time:
            RebootEvent.objects.create(server=server, boot_time=boot_time)
        elif boot_time is not None and server.last_boot_time is None:
            RebootEvent.objects.get_or_create(server=server, boot_time=boot_time)

        server.last_resource_checked = collected_at
        server.last_cpu_percent = cpu_percent
        server.last_ram_percent = ram_percent
        server.last_load_1 = load_1
        server.last_uptime_seconds = uptime_seconds
        server.last_boot_time = boot_time
        server.save(
            update_fields=[
                "last_resource_checked",
                "last_cpu_percent",
                "last_ram_percent",
                "last_load_1",
                "last_uptime_seconds",
                "last_boot_time",
                "last_db_checked",
                "last_db_process_up",
                "last_db_port_ok",
                "last_db_connect_ok",
                "last_db_ping_ms",
                "last_db_connections",
                "last_db_max_connections",
                "last_db_conn_usage_percent",
                "last_db_qps",
                "last_db_read_qps",
                "last_db_write_qps",
                "last_db_tps",
                "last_db_avg_query_ms",
                "last_db_p95_query_ms",
                "last_db_p99_query_ms",
                "last_db_slow_1m",
                "updated_at",
            ]
        )

    channel_layer = get_channel_layer()
    if channel_layer is not None:
        evaluate_alerts_for_server(server=server, now=collected_at, channel_layer=channel_layer)
        async_to_sync(channel_layer.group_send)(
            "status",
            {
                "type": "server.status",
                "server": {
                    "id": server.id,
                    "name": server.name,
                    "pinned": server.pinned,
                    "tags": server.tags,
                    "server_type": server.server_type,
                    "server_type_display": server.get_server_type_display(),
                    "ip_address": server.ip_address,
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
                },
            },
        )

    return JsonResponse({"ok": True, "server_id": server.id, "collected_at": collected_at.isoformat()})


@require_GET
def events_api(request):
    try:
        limit = int(request.GET.get("limit", "50"))
    except ValueError:
        limit = 50
    limit = max(1, min(limit, 200))

    server_id = (request.GET.get("server_id") or "").strip()

    qs = AlertEvent.objects.select_related("server", "rule").order_by("-created_at")
    if server_id:
        try:
            sid = int(server_id)
            qs = qs.filter(server_id=sid)
        except ValueError:
            pass

    rows = list(qs[:limit])
    events = [
        {
            "id": e.id,
            "created_at": e.created_at.isoformat() if e.created_at else None,
            "server": {"id": e.server_id, "name": e.server.name if e.server_id else ""},
            "rule_id": e.rule_id,
            "kind": e.kind,
            "severity": e.severity,
            "is_recovery": e.is_recovery,
            "title": e.title,
            "message": e.message,
            "value": e.value,
            "payload": e.payload,
        }
        for e in rows
    ]

    return JsonResponse({"limit": limit, "events": events})


@require_GET
def resource_series_api(request, server_id: int):
    server = get_object_or_404(Server, pk=server_id)
    range_param, since, limit, max_points = _parse_range_param(request.GET.get("range") or "30")

    qs = ResourceSample.objects.filter(server=server).order_by("collected_at")
    if since is not None:
        qs = qs.filter(collected_at__gte=since)
        rows = list(
            qs.values(
                "collected_at",
                "cpu_percent",
                "ram_percent",
                "load_1",
                "load_5",
                "load_15",
                "uptime_seconds",
            )[:max_points]
        )
    else:
        rows = list(
            qs.values(
                "collected_at",
                "cpu_percent",
                "ram_percent",
                "load_1",
                "load_5",
                "load_15",
                "uptime_seconds",
            )
            .order_by("-collected_at")[:limit]
        )
        rows.reverse()

    points = [
        {
            "collected_at": r["collected_at"].isoformat() if r.get("collected_at") else None,
            "cpu_percent": r.get("cpu_percent"),
            "ram_percent": r.get("ram_percent"),
            "load_1": r.get("load_1"),
            "load_5": r.get("load_5"),
            "load_15": r.get("load_15"),
            "uptime_seconds": r.get("uptime_seconds"),
        }
        for r in rows
    ]

    return JsonResponse(
        {
            "server": {
                "id": server.id,
                "name": server.name,
                "server_type": server.server_type,
                "server_type_display": server.get_server_type_display(),
                "ip_address": server.ip_address,
                "port": server.port,
            },
            "range": range_param,
            "points": points,
        }
    )


@require_GET
def disk_usage_series_api(request, server_id: int):
    server = get_object_or_404(Server, pk=server_id)
    range_param, since, limit, max_points = _parse_range_param(request.GET.get("range") or "30")
    mount_filter = (request.GET.get("mount") or "").strip()

    qs = DiskUsageSample.objects.filter(server=server).order_by("collected_at")
    if mount_filter:
        qs = qs.filter(mount=mount_filter)

    if since is not None:
        qs = qs.filter(collected_at__gte=since)
        rows = list(
            qs.values("collected_at", "mount", "total_bytes", "used_bytes", "percent")[:max_points]
        )
    else:
        rows = list(
            qs.values("collected_at", "mount", "total_bytes", "used_bytes", "percent")
            .order_by("-collected_at")[:limit]
        )
        rows.reverse()

    points = [
        {
            "collected_at": r["collected_at"].isoformat() if r.get("collected_at") else None,
            "mount": r.get("mount"),
            "total_bytes": r.get("total_bytes"),
            "used_bytes": r.get("used_bytes"),
            "percent": r.get("percent"),
        }
        for r in rows
    ]

    return JsonResponse(
        {
            "server": {"id": server.id, "name": server.name},
            "range": range_param,
            "mount": mount_filter or None,
            "points": points,
        }
    )


@require_GET
def disk_io_series_api(request, server_id: int):
    server = get_object_or_404(Server, pk=server_id)
    range_param, since, limit, max_points = _parse_range_param(request.GET.get("range") or "30")

    qs = DiskIOSample.objects.filter(server=server).order_by("collected_at")
    if since is not None:
        qs = qs.filter(collected_at__gte=since)
        rows = list(
            qs.values(
                "collected_at",
                "read_bytes",
                "write_bytes",
                "read_time_ms",
                "write_time_ms",
            )[:max_points]
        )
    else:
        rows = list(
            qs.values(
                "collected_at",
                "read_bytes",
                "write_bytes",
                "read_time_ms",
                "write_time_ms",
            )
            .order_by("-collected_at")[:limit]
        )
        rows.reverse()

    points = [
        {
            "collected_at": r["collected_at"].isoformat() if r.get("collected_at") else None,
            "read_bytes": r.get("read_bytes"),
            "write_bytes": r.get("write_bytes"),
            "read_time_ms": r.get("read_time_ms"),
            "write_time_ms": r.get("write_time_ms"),
        }
        for r in rows
    ]

    return JsonResponse(
        {
            "server": {"id": server.id, "name": server.name},
            "range": range_param,
            "points": points,
        }
    )


@require_GET
def db_series_api(request, server_id: int):
    server = get_object_or_404(Server, pk=server_id)
    range_param, since, limit, max_points = _parse_range_param(request.GET.get("range") or "30")

    qs = DbSample.objects.filter(server=server).order_by("collected_at")
    if since is not None:
        qs = qs.filter(collected_at__gte=since)
        rows = list(
            qs.values(
                "collected_at",
                "process_up",
                "port_ok",
                "connect_ok",
                "ping_ms",
                "current_connections",
                "max_connections",
                "connection_usage_percent",
                "qps",
                "read_qps",
                "write_qps",
                "tps",
                "avg_query_ms",
                "p95_query_ms",
                "p99_query_ms",
                "slow_queries_1m",
            )[:max_points]
        )
    else:
        rows = list(
            qs.values(
                "collected_at",
                "process_up",
                "port_ok",
                "connect_ok",
                "ping_ms",
                "current_connections",
                "max_connections",
                "connection_usage_percent",
                "qps",
                "read_qps",
                "write_qps",
                "tps",
                "avg_query_ms",
                "p95_query_ms",
                "p99_query_ms",
                "slow_queries_1m",
            )
            .order_by("-collected_at")[:limit]
        )
        rows.reverse()

    points = [
        {
            "collected_at": r["collected_at"].isoformat() if r.get("collected_at") else None,
            "process_up": r.get("process_up"),
            "port_ok": r.get("port_ok"),
            "connect_ok": r.get("connect_ok"),
            "ping_ms": r.get("ping_ms"),
            "current_connections": r.get("current_connections"),
            "max_connections": r.get("max_connections"),
            "connection_usage_percent": r.get("connection_usage_percent"),
            "qps": r.get("qps"),
            "read_qps": r.get("read_qps"),
            "write_qps": r.get("write_qps"),
            "tps": r.get("tps"),
            "avg_query_ms": r.get("avg_query_ms"),
            "p95_query_ms": r.get("p95_query_ms"),
            "p99_query_ms": r.get("p99_query_ms"),
            "slow_queries_1m": r.get("slow_queries_1m"),
        }
        for r in rows
    ]

    return JsonResponse(
        {
            "server": {"id": server.id, "name": server.name},
            "range": range_param,
            "points": points,
        }
    )


@require_GET
def network_series_api(request, server_id: int):
    server = get_object_or_404(Server, pk=server_id)
    range_param, since, limit, max_points = _parse_range_param(request.GET.get("range") or "30")

    qs = NetworkSample.objects.filter(server=server).order_by("collected_at")
    if since is not None:
        qs = qs.filter(collected_at__gte=since)
        rows = list(
            qs.values(
                "collected_at",
                "bytes_sent",
                "bytes_recv",
                "packets_sent",
                "packets_recv",
                "errin",
                "errout",
                "dropin",
                "dropout",
            )[:max_points]
        )
    else:
        rows = list(
            qs.values(
                "collected_at",
                "bytes_sent",
                "bytes_recv",
                "packets_sent",
                "packets_recv",
                "errin",
                "errout",
                "dropin",
                "dropout",
            )
            .order_by("-collected_at")[:limit]
        )
        rows.reverse()

    points = [
        {
            "collected_at": r["collected_at"].isoformat() if r.get("collected_at") else None,
            "bytes_sent": r.get("bytes_sent"),
            "bytes_recv": r.get("bytes_recv"),
            "packets_sent": r.get("packets_sent"),
            "packets_recv": r.get("packets_recv"),
            "errin": r.get("errin"),
            "errout": r.get("errout"),
            "dropin": r.get("dropin"),
            "dropout": r.get("dropout"),
        }
        for r in rows
    ]

    return JsonResponse(
        {
            "server": {"id": server.id, "name": server.name},
            "range": range_param,
            "points": points,
        }
    )


@require_GET
def reboot_history_api(request, server_id: int):
    server = get_object_or_404(Server, pk=server_id)

    try:
        limit = int(request.GET.get("limit", "20"))
    except ValueError:
        limit = 20
    limit = max(1, min(limit, 200))

    qs = RebootEvent.objects.filter(server=server).order_by("-boot_time")[:limit]
    events = [
        {
            "boot_time": e.boot_time.isoformat() if e.boot_time else None,
            "detected_at": e.detected_at.isoformat() if e.detected_at else None,
        }
        for e in qs
    ]

    return JsonResponse(
        {
            "server": {"id": server.id, "name": server.name},
            "limit": limit,
            "events": events,
        }
    )


def server_detail(request, server_id: int):
    server = get_object_or_404(Server, pk=server_id)
    return render(request, "monitor/server_detail.html", {"server": server})


@require_GET
def server_series_api(request, server_id: int):
    server = get_object_or_404(Server, pk=server_id)

    range_param, since, limit, max_points = _parse_range_param(request.GET.get("range") or "30")

    qs = CheckResult.objects.filter(server=server).order_by("checked_at")

    if since is not None:
        qs = qs.filter(checked_at__gte=since)
        points = list(qs.values("checked_at", "status", "http_ok", "latency_ms", "http_status_code")[:max_points])
    else:
        if limit is None:
            limit = 30
        limit = max(1, min(limit, max_points))
        points = list(qs.values("checked_at", "status", "http_ok", "latency_ms", "http_status_code").order_by("-checked_at")[:limit])
        points.reverse()

    payload = [
        {
            "checked_at": p["checked_at"].isoformat() if p["checked_at"] else None,
            "status": p["status"],
            "http_ok": p.get("http_ok"),
            "latency_ms": p["latency_ms"],
            "http_status_code": p["http_status_code"],
        }
        for p in points
    ]

    return JsonResponse(
        {
            "server": {
                "id": server.id,
                "name": server.name,
                "server_type": server.server_type,
                "server_type_display": server.get_server_type_display(),
                "ip_address": server.ip_address,
                "port": server.port,
            },
            "range": range_param,
            "points": payload,
        }
    )


@require_http_methods(["GET", "POST"])
def server_add(request):
    if request.method == "POST":
        form = ServerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("dashboard")
    else:
        form = ServerForm()

    return render(
        request,
        "monitor/server_form.html",
        {
            "form": form,
            "mode": "add",
        },
    )


@require_http_methods(["GET", "POST"])
def server_edit(request, server_id: int):
    server = get_object_or_404(Server, pk=server_id)
    if request.method == "POST":
        form = ServerForm(request.POST, instance=server)
        if form.is_valid():
            form.save()
            return redirect("dashboard")
    else:
        form = ServerForm(instance=server)

    return render(
        request,
        "monitor/server_form.html",
        {
            "form": form,
            "server": server,
            "mode": "edit",
        },
    )


@require_http_methods(["GET", "POST"])
def server_delete(request, server_id: int):
    server = get_object_or_404(Server, pk=server_id)
    if request.method == "POST":
        server.delete()
        return redirect("dashboard")

    return render(request, "monitor/server_confirm_delete.html", {"server": server})


# ISP Management Views
@require_http_methods(["GET", "POST"])
def isp_add(request):
    """Add a new ISP connection"""
    if request.method == "POST":
        form = ISPConnectionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("network_dashboard")
    else:
        form = ISPConnectionForm()

    return render(
        request,
        "monitor/isp_form.html",
        {
            "form": form,
            "mode": "add",
        },
    )


@require_http_methods(["GET", "POST"])
def isp_edit(request, isp_id: int):
    """Edit an ISP connection"""
    isp = get_object_or_404(ISPConnection, pk=isp_id)
    if request.method == "POST":
        form = ISPConnectionForm(request.POST, instance=isp)
        if form.is_valid():
            form.save()
            return redirect("network_dashboard")
    else:
        form = ISPConnectionForm(instance=isp)

    return render(
        request,
        "monitor/isp_form.html",
        {
            "form": form,
            "isp": isp,
            "mode": "edit",
        },
    )


@require_http_methods(["GET", "POST"])
def isp_delete(request, isp_id: int):
    """Delete an ISP connection"""
    isp = get_object_or_404(ISPConnection, pk=isp_id)
    if request.method == "POST":
        isp.delete()
        return redirect("network_dashboard")

    return render(request, "monitor/isp_confirm_delete.html", {"isp": isp})


@require_GET
def isp_detail(request, isp_id: int):
    """Detailed view of an ISP connection"""
    isp = get_object_or_404(ISPConnection, pk=isp_id)
    
    # Get metrics history (last 24 hours)
    since = timezone.now() - timedelta(hours=24)
    metrics_history = ISPMetric.objects.filter(
        connection=isp, 
        timestamp__gte=since
    ).order_by("timestamp")
    
    # Group metrics by name for charts
    metrics_by_name = {}
    for metric in metrics_history:
        if metric.metric_name not in metrics_by_name:
            metrics_by_name[metric.metric_name] = []
        metrics_by_name[metric.metric_name].append({
            'timestamp': metric.timestamp.isoformat(),
            'value': metric.value,
            'unit': metric.unit,
        })
    
    # Convert metrics data to JSON for JavaScript
    import json
    metrics_json = json.dumps(metrics_by_name)
    
    # Get failover events for this ISP
    failover_events = ISPFailover.objects.filter(
        primary_isp=isp
    ).order_by("-failover_time")[:50]
    
    # Calculate health score for this specific ISP
    from monitor.isp_monitor import get_individual_isp_health_score
    health_score = get_individual_isp_health_score(isp)
    
    context = {
        "isp": isp,
        "metrics_by_name": metrics_by_name,
        "metrics_json": metrics_json,
        "failover_events": failover_events,
        "health_score": health_score,
    }
    
    return render(request, "monitor/isp_detail.html", context)


@require_GET
def isp_status_api(request):
    """API endpoint for ISP status"""
    connections = ISPConnection.objects.filter(enabled=True).order_by("-primary_connection", "name")
    payload = []
    
    for isp in connections:
        # Get latest metrics
        latest_metrics = ISPMetric.objects.filter(connection=isp).order_by("-timestamp")[:10]
        metrics_dict = {}
        for metric in latest_metrics:
            if metric.metric_name not in metrics_dict:
                metrics_dict[metric.metric_name] = {
                    'value': metric.value,
                    'unit': metric.unit,
                    'timestamp': metric.timestamp.isoformat() if metric.timestamp else None,
                }
        
        status = _calculate_isp_status(metrics_dict)
        
        payload.append({
            "id": isp.id,
            "name": isp.name,
            "isp_type": isp.isp_type,
            "isp_type_display": isp.get_isp_type_display(),
            "gateway_ip": str(isp.gateway_ip),
            "bandwidth_mbps": isp.bandwidth_mbps,
            "primary_connection": isp.primary_connection,
            "enabled": isp.enabled,
            "last_checked": isp.last_checked.isoformat() if isp.last_checked else None,
            "status": status,
            "metrics": metrics_dict,
        })
    
    return JsonResponse({"isp_connections": payload})


@require_GET
def isp_metrics_api(request, isp_id: int):
    """API endpoint for ISP metrics history"""
    isp = get_object_or_404(ISPConnection, pk=isp_id)
    range_param, since, limit, max_points = _parse_range_param(request.GET.get("range") or "30")
    
    qs = ISPMetric.objects.filter(connection=isp).order_by("timestamp")
    
    if since is not None:
        qs = qs.filter(timestamp__gte=since)
        rows = list(qs.values("timestamp", "metric_name", "value", "unit")[:max_points])
    else:
        rows = list(qs.values("timestamp", "metric_name", "value", "unit").order_by("-timestamp")[:limit])
        rows.reverse()
    
    # Group by metric name
    metrics_by_name = {}
    for row in rows:
        metric_name = row["metric_name"]
        if metric_name not in metrics_by_name:
            metrics_by_name[metric_name] = []
        metrics_by_name[metric_name].append({
            "timestamp": row["timestamp"].isoformat() if row["timestamp"] else None,
            "value": row["value"],
            "unit": row["unit"],
        })
    
    return JsonResponse({
        "isp": {
            "id": isp.id,
            "name": isp.name,
            "isp_type": isp.isp_type,
            "isp_type_display": isp.get_isp_type_display(),
        },
        "range": range_param,
        "metrics": metrics_by_name,
    })


def monitoring_mode(request):
    """Monitoring mode page with network overview and event timeline"""
    servers = Server.objects.all().order_by("-pinned", "name")
    network_devices = NetworkDevice.objects.filter(enabled=True).order_by("name")
    
    # Get recent events for timeline
    recent_events = AlertEvent.objects.select_related('server', 'rule').order_by("-created_at")[:50]
    recent_security_events = SecurityEvent.objects.select_related('device').order_by("-timestamp")[:20]
    
    # Calculate server statistics
    total_servers = servers.count()
    enabled_servers = servers.filter(enabled=True).count()
    up_servers = servers.filter(last_status=Server.STATUS_UP, enabled=True).count()
    down_servers = servers.filter(last_status=Server.STATUS_DOWN, enabled=True).count()
    unknown_servers = servers.filter(last_status=Server.STATUS_UNKNOWN, enabled=True).count()
    
    # Calculate network device statistics
    total_devices = network_devices.count()
    online_devices = network_devices.count()  # We'll determine this from recent metrics
    
    # Get latest network metrics for each device
    device_metrics = {}
    for device in network_devices:
        latest_metrics = NetworkMetric.objects.filter(device=device).order_by("-timestamp")[:10]
        if latest_metrics:
            device_metrics[device.id] = {m.metric_name: m.value for m in latest_metrics}
    
    # Group servers by type
    servers_by_type = {}
    for server in servers:
        server_type = server.get_server_type_display()
        if server_type not in servers_by_type:
            servers_by_type[server_type] = []
        servers_by_type[server_type].append(server)
    
    # Group network devices by type (excluding firewall from SSL monitoring)
    devices_by_type = {}
    for device in network_devices:
        device_type = device.get_device_type_display()
        if device_type not in devices_by_type:
            devices_by_type[device_type] = []
        devices_by_type[device_type].append(device)
    
    # Get SSL certificate information for web servers and routers only (excluding firewalls) - WITH CACHING
    from monitor.services.ssl_cache_service import get_cached_ssl_certificates
    
    try:
        ssl_certificates, ssl_summary = get_cached_ssl_certificates()
        logger.info(f"SSL certificates loaded from cache for {len(ssl_certificates)} devices")
    except Exception as e:
        logger.error(f"Error loading SSL certificates from cache: {e}")
        # Fallback to original method
        ssl_certificates = {}
        ssl_summary = {
            'total': 0,
            'good': 0,
            'warning': 0,
            'critical': 0,
            'expired': 0,
            'error': 0
        }
        
        ssl_devices = network_devices.filter(device_type__in=['WEB_SERVER', 'ROUTER'])  # Removed FIREWALL
        for device in ssl_devices:
            device_ssl = get_ssl_certificates_for_device(device)
            if device_ssl:
                ssl_certificates[device.id] = device_ssl
                ssl_summary['total'] += len(device_ssl)
                
                # Count certificate statuses
                for port, cert in device_ssl.items():
                    status = cert.get('status', 'error')
                    if status in ssl_summary:
                        ssl_summary[status] += 1
    
    context = {
        "servers": servers,
        "network_devices": network_devices,
        "recent_events": recent_events,
        "recent_security_events": recent_security_events,
        "total_servers": total_servers,
        "enabled_servers": enabled_servers,
        "up_servers": up_servers,
        "down_servers": down_servers,
        "unknown_servers": unknown_servers,
        "total_devices": total_devices,
        "online_devices": online_devices,
        "servers_by_type": servers_by_type,
        "devices_by_type": devices_by_type,
        "device_metrics": device_metrics,
        "ssl_certificates": ssl_certificates,
        "ssl_summary": ssl_summary,
        "uptime_percentage": round((up_servers / enabled_servers * 100) if enabled_servers > 0 else 0, 1),
        "active_nav": "monitoring",
    }
    
    return render(request, "monitor/monitoring_mode.html", context)


@require_GET
def network_devices(request):
    """Network devices and network device discovery page"""
    # Get filter parameters
    network_filter = request.GET.get('network', '')
    device_type_filter = request.GET.get('device_type', '')
    active_filter = request.GET.get('active', '')
    
    # Start with base queryset
    network_devices = NetworkDevice.objects.filter(enabled=True).order_by("name")
    
    # Apply filters
    if network_filter:
        network_devices = network_devices.filter(network=network_filter)
    
    if device_type_filter:
        network_devices = network_devices.filter(device_type=device_type_filter)
    
    if active_filter:
        network_devices = network_devices.filter(is_active=(active_filter.lower() == 'true'))
    
    # Get available networks for filter dropdown
    available_networks = NetworkDevice.objects.filter(
        enabled=True, 
        network__isnull=False
    ).values_list('network', flat=True).distinct().order_by('network')
    
    # Get device statistics
    device_stats = {}
    for device in network_devices:
        # Get latest metrics
        latest_metrics = NetworkMetric.objects.filter(device=device).order_by("-timestamp")[:20]
        metrics_dict = {}
        for metric in latest_metrics:
            if metric.metric_name not in metrics_dict:
                metrics_dict[metric.metric_name] = {
                    'value': metric.value,
                    'unit': metric.unit,
                    'timestamp': metric.timestamp,
                }
        
        # Get interface status
        interfaces = NetworkInterface.objects.filter(device=device)
        interface_stats = []
        for interface in interfaces:
            # Get latest traffic data
            latest_traffic = TrafficLog.objects.filter(interface=interface).order_by("-timestamp").first()
            interface_stats.append({
                'name': interface.name,
                'status': interface.status,
                'speed': interface.speed,
                'latest_traffic': latest_traffic,
            })
        
        device_stats[device.id] = {
            'metrics': metrics_dict,
            'interfaces': interface_stats,
            'last_checked': device.last_checked,
        }
    
    # Get recent security events
    recent_events = SecurityEvent.objects.select_related('device').order_by("-timestamp")[:30]
    
    context = {
        "network_devices": network_devices,
        "device_stats": device_stats,
        "recent_events": recent_events,
        "available_networks": available_networks,
        "current_filters": {
            "network": network_filter,
            "device_type": device_type_filter,
            "active": active_filter,
        }
    }
    
    return render(request, "monitor/network_devices.html", context)


@require_GET
def network_dashboard(request):
    """Enhanced network dashboard with ISP monitoring"""
    network_devices = NetworkDevice.objects.filter(enabled=True).order_by("name")
    isp_connections = ISPConnection.objects.filter(enabled=True).order_by("-primary_connection", "name")
    
    # Get device statistics
    device_stats = {}
    for device in network_devices:
        # Get latest metrics
        latest_metrics = NetworkMetric.objects.filter(device=device).order_by("-timestamp")[:20]
        metrics_dict = {}
        for metric in latest_metrics:
            if metric.metric_name not in metrics_dict:
                metrics_dict[metric.metric_name] = {
                    'value': metric.value,
                    'unit': metric.unit,
                    'timestamp': metric.timestamp,
                }
        
        # Get interface status
        interfaces = NetworkInterface.objects.filter(device=device)
        interface_stats = []
        for interface in interfaces:
            # Get latest traffic data
            latest_traffic = TrafficLog.objects.filter(interface=interface).order_by("-timestamp").first()
            interface_stats.append({
                'name': interface.name,
                'status': interface.status,
                'speed': interface.speed,
                'latest_traffic': latest_traffic,
            })
        
        device_stats[device.id] = {
            'metrics': metrics_dict,
            'interfaces': interface_stats,
            'last_checked': device.last_checked,
        }
    
    # Get ISP statistics
    isp_stats = {}
    for isp in isp_connections:
        latest_metrics = ISPMetric.objects.filter(connection=isp).order_by("-timestamp")[:10]
        metrics_dict = {}
        for metric in latest_metrics:
            if metric.metric_name not in metrics_dict:
                metrics_dict[metric.metric_name] = {
                    'value': metric.value,
                    'unit': metric.unit,
                    'timestamp': metric.timestamp,
                }
        
        isp_stats[isp.id] = {
            'metrics': metrics_dict,
            'last_checked': isp.last_checked,
            'status': _calculate_isp_status(metrics_dict),
        }
    
    # Get recent security events
    recent_events = SecurityEvent.objects.select_related('device').order_by("-timestamp")[:30]
    recent_failovers = ISPFailover.objects.order_by("-failover_time")[:10]
    
    context = {
        "network_devices": network_devices,
        "isp_connections": isp_connections,
        "device_stats": device_stats,
        "isp_stats": isp_stats,
        "recent_events": recent_events,
        "recent_failovers": recent_failovers,
        "active_nav": "network",
    }
    
    return render(request, "monitor/network_dashboard.html", context)


def _calculate_isp_status(metrics):
    """Calculate ISP status based on metrics"""
    if not metrics:
        return "unknown"
    
    latency = metrics.get('latency_ms', {}).get('value')
    packet_loss = metrics.get('packet_loss_percent', {}).get('value')
    internet_status = metrics.get('internet_status', {}).get('value')
    dns_status = metrics.get('dns_status', {}).get('value')
    
    # Priority-based status calculation
    if internet_status == 0:
        return "critical"
    elif dns_status == 0:
        return "critical"
    elif packet_loss and packet_loss > 20:
        return "critical"
    elif packet_loss and packet_loss > 10 or (latency and latency > 200):
        return "degraded"
    elif packet_loss and packet_loss > 5 or (latency and latency > 100):
        return "warning"
    else:
        return "healthy"


@require_GET
def device_detail(request, device_id):
    """Detailed view of a network device"""
    device = get_object_or_404(NetworkDevice, id=device_id)
    
    # Get metrics history (last 24 hours)
    since = timezone.now() - timedelta(hours=24)
    metrics_history = NetworkMetric.objects.filter(
        device=device, 
        timestamp__gte=since
    ).order_by("timestamp")
    
    # Group metrics by name for charts
    metrics_by_name = {}
    for metric in metrics_history:
        if metric.metric_name not in metrics_by_name:
            metrics_by_name[metric.metric_name] = []
        metrics_by_name[metric.metric_name].append({
            'timestamp': metric.timestamp.isoformat(),
            'value': metric.value,
            'unit': metric.unit,
        })
    
    # Get interfaces and their traffic history
    interfaces = NetworkInterface.objects.filter(device=device)
    interface_data = []
    for interface in interfaces:
        # Get traffic history (last 24 hours)
        traffic_history = TrafficLog.objects.filter(
            interface=interface,
            timestamp__gte=since
        ).order_by("timestamp")
        
        interface_data.append({
            'interface': interface,
            'traffic_history': [
                {
                    'timestamp': log.timestamp.isoformat(),
                    'bytes_in': log.bytes_in,
                    'bytes_out': log.bytes_out,
                    'packets_in': log.packets_in,
                    'packets_out': log.packets_out,
                }
                for log in traffic_history
            ],
        })
    
    # Get security events for this device
    security_events = SecurityEvent.objects.filter(
        device=device
    ).order_by("-timestamp")[:100]
    
    # Get SSL certificate information for web servers
    ssl_certificates = {}
    if device.device_type in ['WEB_SERVER', 'FIREWALL', 'ROUTER']:
        ssl_certificates = get_ssl_certificates_for_device(device)
    
    context = {
        "device": device,
        "metrics_by_name": metrics_by_name,
        "interface_data": interface_data,
        "security_events": security_events,
        "ssl_certificates": ssl_certificates,
    }
    
    return render(request, "monitor/device_detail.html", context)


def get_ssl_certificates_for_device(device) -> Dict:
    """Get SSL certificate information for a device"""
    logger.debug(f"Starting SSL certificate check for device: {device.name} (ID: {device.id}, IP: {device.ip_address})")
    try:
        ssl_info = {}
        
        # Check if this device has SSH credentials for remote SSL monitoring
        ssh_monitored_ips = ['192.168.254.13', '192.168.254.50', '192.168.253.15']
        
        if device.ip_address in ssh_monitored_ips:
            logger.debug(f"Attempting remote SSH SSL monitoring for {device.ip_address}")
            # Use remote SSH monitoring for these specific servers
            from monitor.services.remote_ssl_certificate_monitor import RemoteSSLCertificateMonitor
            
            remote_monitor = RemoteSSLCertificateMonitor()
            remote_cert = remote_monitor.get_remote_ssl_info(device.ip_address)
            logger.debug(f"Raw remote SSH cert info for {device.ip_address}: {remote_cert}")
            
            if remote_cert:
                formatted_info = remote_monitor.format_certificate_info(remote_cert)
                ssl_info["443"] = formatted_info
                
                logger.info(f"Remote SSL certificate monitored for {device.ip_address} via SSH - "
                          f"Status: {formatted_info.get('status')}, "
                          f"Days remaining: {formatted_info.get('days_remaining')}")
        else:
            logger.debug(f"Attempting standard SSL monitoring for {device.ip_address}")
            # Use standard SSL monitoring for other devices
            from monitor.services.ssl_certificate_monitor import SSLCertificateMonitor
            
            ssl_monitor = SSLCertificateMonitor()
            
            # Check common HTTPS ports
            https_ports = [443, 8443, 9443, 4443]  # Include common management ports
            
            # Add device-specific ports if available (check if attribute exists)
            if hasattr(device, 'common_ports') and device.common_ports:
                device_common_ports = [int(p) for p in device.common_ports.split(',') if p.strip().isdigit()]
                https_ports.extend([port for port in device_common_ports if port in [443, 8443, 9443]])
            
            # Remove duplicates
            https_ports = list(set(https_ports))
            logger.debug(f"Checking ports: {https_ports} for {device.ip_address}")
            
            for port in https_ports:
                try:
                    logger.debug(f"Checking {device.ip_address}:{port}...")
                    cert_info = ssl_monitor.get_ssl_info(device.ip_address, port)
                    logger.debug(f"Raw cert info for {device.ip_address}:{port}: {cert_info}")
                    if cert_info:
                        formatted_info = ssl_monitor.format_certificate_info(cert_info)
                        ssl_info[f"{port}"] = formatted_info
                        
                        logger.info(f"SSL certificate monitored for {device.ip_address}:{port} - "
                                  f"Status: {formatted_info.get('status')}, "
                                  f"Days remaining: {formatted_info.get('days_remaining')}")
                        
                except Exception as e:
                    logger.warning(f"Failed to monitor SSL certificate for {device.ip_address}:{port} - {e}")
                    ssl_info[f"{port}"] = {
                        'hostname': device.ip_address,
                        'port': port,
                        'status': 'error',
                        'status_color': '#6c757d',
                        'error': str(e)
                    }
        
        return ssl_info
        
    except Exception as e:
        logger.error(f"Error getting SSL certificates for {device.name} (ID: {device.id}, IP: {device.ip_address}): {e}", exc_info=True)
        return {}


# Network Device Discovery API Endpoints

@require_GET
def firewall_interfaces_api(request, device_id):
    """API endpoint to get real-time firewall interface data"""
    device = get_object_or_404(NetworkDevice, id=device_id)
    
    # Only provide interface data for firewall devices
    if device.device_type != 'FIREWALL' or device.ip_address != '192.168.253.2':
        return JsonResponse({'error': 'Interface monitoring only available for Sophos Firewall'}, status=400)
    
    try:
        monitor = FirewallInterfaceMonitor()
        interfaces = monitor.get_interfaces()
        
        return JsonResponse({
            'success': True,
            'interfaces': interfaces,
            'timestamp': timezone.now().isoformat(),
            'device_name': device.name
        })
        
    except Exception as e:
        logger.error(f"Error getting firewall interfaces: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_GET
def network_devices_api(request):
    """API endpoint to list all network devices"""
    devices = NetworkDevice.objects.all()
    
    network_filter = request.GET.get('network')
    device_type_filter = request.GET.get('device_type')
    is_active_filter = request.GET.get('is_active')
    sort_by = request.GET.get('sort', 'ip')  # Default sort by IP
    
    if network_filter:
        devices = devices.filter(network=network_filter)
    if device_type_filter:
        devices = devices.filter(device_type=device_type_filter)
    if is_active_filter is not None:
        devices = devices.filter(is_active=is_active_filter.lower() == 'true')
    
    # Apply sorting
    if sort_by == 'ip':
        # Sort by IP address numerically
        devices = sorted(devices, key=lambda d: tuple(map(int, d.ip_address.split('.'))))
    elif sort_by == 'name':
        devices = devices.order_by('name')
    elif sort_by == 'type':
        devices = devices.order_by('device_type', 'name')
    elif sort_by == 'status':
        devices = devices.order_by('-is_active', 'name')
    else:
        # Default to IP sorting
        devices = sorted(devices, key=lambda d: tuple(map(int, d.ip_address.split('.'))))
    
    payload = [
        {
            "id": d.id,
            "name": d.name,
            "device_type": d.device_type,
            "device_type_display": d.get_device_type_display(),
            "ip_address": d.ip_address,
            "mac_address": d.mac_address,
            "vendor": d.vendor,
            "hostname": d.hostname,
            "network": d.network,
            "os_fingerprint": d.os_fingerprint,
            "open_ports": d.open_ports,
            "is_active": d.is_active,
            "auto_discovered": d.auto_discovered,
            "enabled": d.enabled,
            "first_seen": d.first_seen.isoformat() if d.first_seen else None,
            "last_seen": d.last_seen.isoformat() if d.last_seen else None,
            "last_checked": d.last_checked.isoformat() if d.last_checked else None,
            "notes": d.notes,
        }
        for d in devices
    ]
    
    return JsonResponse({"devices": payload})


@csrf_exempt
@require_http_methods(["POST"])
def scan_network_api(request):
    """API endpoint to trigger network scanning"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid_json"}, status=400)
    
    network_range = data.get('network_range')
    timeout = data.get('timeout', 3)
    max_threads = data.get('max_threads', 50)
    update_existing = data.get('update_existing', False)
    
    if not network_range:
        scanner = NetworkScanner(timeout=timeout, max_threads=max_threads)
        networks = scanner.get_local_networks()
        if not networks:
            return JsonResponse({"error": "no_network_range_specified"}, status=400)
        network_range = networks[0]
    
    try:
        scanner = NetworkScanner(timeout=timeout, max_threads=max_threads)
        devices = scanner.scan_network(network_range)
        
        total_created = 0
        total_updated = 0
        
        for device_info in devices:
            # Check if device already exists
            existing_device = None
            if device_info['mac_address']:
                existing_device = NetworkDevice.objects.filter(
                    mac_address=device_info['mac_address']
                ).first()
            
            if not existing_device:
                existing_device = NetworkDevice.objects.filter(
                    ip_address=device_info['ip_address']
                ).first()
            
            if existing_device:
                if update_existing:
                    # Update existing device
                    existing_device.ip_address = device_info['ip_address']
                    existing_device.mac_address = device_info['mac_address']
                    existing_device.vendor = device_info['vendor']
                    existing_device.hostname = device_info['hostname']
                    existing_device.device_type = device_info['device_type']
                    existing_device.open_ports = device_info['open_ports']
                    existing_device.last_seen = timezone.now()
                    existing_device.is_active = True
                    existing_device.save()
                    total_updated += 1
                else:
                    # Just update last_seen
                    existing_device.last_seen = timezone.now()
                    existing_device.is_active = True
                    existing_device.save()
            else:
                # Create new device
                device_name = device_info['hostname'] or f"Device-{device_info['ip_address'].split('.')[-1]}"
                
                # Ensure name is unique
                base_name = device_name
                counter = 1
                while NetworkDevice.objects.filter(name=device_name).exists():
                    device_name = f"{base_name}-{counter}"
                    counter += 1
                
                NetworkDevice.objects.create(
                    name=device_name,
                    device_type=device_info['device_type'],
                    ip_address=device_info['ip_address'],
                    mac_address=device_info['mac_address'],
                    vendor=device_info['vendor'],
                    hostname=device_info['hostname'],
                    open_ports=device_info['open_ports'],
                    auto_discovered=True,
                    is_active=True,
                )
                total_created += 1
        
        return JsonResponse({
            "success": True,
            "network_range": network_range,
            "devices_found": len(devices),
            "devices_created": total_created,
            "devices_updated": total_updated,
            "devices": devices
        })
        
    except Exception as e:
        logger.error(f"Network scan failed: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@require_GET
def network_scan_status_api(request):
    """API endpoint to get network scanning statistics"""
    total_devices = NetworkDevice.objects.count()
    active_devices = NetworkDevice.objects.filter(is_active=True).count()
    auto_discovered = NetworkDevice.objects.filter(auto_discovered=True).count()
    
    # Count by device type
    device_types = {}
    for device_type, display_name in NetworkDevice.TYPE_CHOICES:
        count = NetworkDevice.objects.filter(device_type=device_type).count()
        if count > 0:
            device_types[device_type] = {
                "count": count,
                "display_name": display_name
            }
    
    # Recently discovered devices (last 24 hours)
    since = timezone.now() - timedelta(hours=24)
    recent_discoveries = NetworkDevice.objects.filter(
        first_seen__gte=since
    ).order_by("-first_seen")[:10]
    
    recent_devices = [
        {
            "id": d.id,
            "name": d.name,
            "device_type": d.device_type,
            "device_type_display": d.get_device_type_display(),
            "ip_address": d.ip_address,
            "first_seen": d.first_seen.isoformat() if d.first_seen else None,
        }
        for d in recent_discoveries
    ]
    
    return JsonResponse({
        "total_devices": total_devices,
        "active_devices": active_devices,
        "auto_discovered": auto_discovered,
        "device_types": device_types,
        "recent_discoveries": recent_devices,
    })


@csrf_exempt
@require_http_methods(["POST", "DELETE"])
def network_device_api(request, device_id=None):
    """API endpoint for individual network device operations"""
    if device_id:
        device = get_object_or_404(NetworkDevice, id=device_id)
    
    if request.method == "POST":
        if device_id:
            # Update existing device
            try:
                data = json.loads(request.body)
                
                # Update allowed fields
                allowed_fields = [
                    'name', 'device_type', 'ip_address', 'mac_address',
                    'vendor', 'hostname', 'os_fingerprint', 'notes',
                    'enabled', 'is_active'
                ]
                
                for field in allowed_fields:
                    if field in data:
                        setattr(device, field, data[field])
                
                if 'open_ports' in data:
                    device.open_ports = data['open_ports']
                
                device.save()
                
                return JsonResponse({
                    "success": True,
                    "device": {
                        "id": device.id,
                        "name": device.name,
                        "device_type": device.device_type,
                        "device_type_display": device.get_device_type_display(),
                        "ip_address": device.ip_address,
                        "mac_address": device.mac_address,
                        "vendor": device.vendor,
                        "hostname": device.hostname,
                        "is_active": device.is_active,
                        "enabled": device.enabled,
                    }
                })
                
            except json.JSONDecodeError:
                return JsonResponse({"error": "invalid_json"}, status=400)
            except Exception as e:
                return JsonResponse({"error": str(e)}, status=500)
        else:
            # Create new device
            try:
                data = json.loads(request.body)
                
                # Validate required fields
                if not data.get('name') or not data.get('ip_address'):
                    return JsonResponse({"error": "name and ip_address are required"}, status=400)
                
                # Ensure name is unique
                if NetworkDevice.objects.filter(name=data['name']).exists():
                    return JsonResponse({"error": "device with this name already exists"}, status=400)
                
                device = NetworkDevice.objects.create(
                    name=data['name'],
                    device_type=data.get('device_type', NetworkDevice.TYPE_UNKNOWN),
                    ip_address=data['ip_address'],
                    mac_address=data.get('mac_address'),
                    vendor=data.get('vendor'),
                    hostname=data.get('hostname'),
                    os_fingerprint=data.get('os_fingerprint'),
                    open_ports=data.get('open_ports', {}),
                    auto_discovered=False,  # Manually created
                    is_active=data.get('is_active', True),
                    enabled=data.get('enabled', True),
                    notes=data.get('notes'),
                )
                
                return JsonResponse({
                    "success": True,
                    "device": {
                        "id": device.id,
                        "name": device.name,
                        "device_type": device.device_type,
                        "device_type_display": device.get_device_type_display(),
                        "ip_address": device.ip_address,
                        "mac_address": device.mac_address,
                        "vendor": device.vendor,
                        "hostname": device.hostname,
                        "is_active": device.is_active,
                        "enabled": device.enabled,
                    }
                })
                
            except json.JSONDecodeError:
                return JsonResponse({"error": "invalid_json"}, status=400)
            except Exception as e:
                return JsonResponse({"error": str(e)}, status=500)
    
    elif request.method == "DELETE":
        if device_id:
            device.delete()
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"error": "device_id required for DELETE"}, status=400)


# Bandwidth Monitoring API Endpoints

@require_GET
def device_bandwidth_api(request, device_id):
    """API endpoint to get bandwidth history for a specific device"""
    device = get_object_or_404(NetworkDevice, id=device_id)
    
    # Parse time range parameter
    hours = int(request.GET.get('hours', 24))
    since = timezone.now() - timedelta(hours=hours)
    
    # Get bandwidth measurements
    measurements = DeviceBandwidthMeasurement.objects.filter(
        device=device,
        timestamp__gte=since
    ).order_by('timestamp')
    
    # Group by interface
    interface_data = {}
    for measurement in measurements:
        interface = measurement.interface or 'default'
        if interface not in interface_data:
            interface_data[interface] = []
        
        interface_data[interface].append({
            'timestamp': measurement.timestamp.isoformat(),
            'bps_in': measurement.bps_in,
            'bps_out': measurement.bps_out,
            'total_bps': measurement.total_bps,
            'mbps_in': measurement.mbps_in,
            'mbps_out': measurement.mbps_out,
            'total_mbps': measurement.total_mbps,
            'pps_in': measurement.pps_in,
            'pps_out': measurement.pps_out,
            'total_pps': measurement.total_pps,
        })
    
    # Get latest measurement
    latest_measurement = measurements.first()
    
    return JsonResponse({
        'device': {
            'id': device.id,
            'name': device.name,
            'ip_address': device.ip_address,
            'device_type': device.device_type,
            'device_type_display': device.get_device_type_display(),
        },
        'latest': {
            'timestamp': latest_measurement.timestamp.isoformat() if latest_measurement else None,
            'total_mbps': latest_measurement.total_mbps if latest_measurement else 0,
            'mbps_in': latest_measurement.mbps_in if latest_measurement else 0,
            'mbps_out': latest_measurement.mbps_out if latest_measurement else 0,
            'total_pps': latest_measurement.total_pps if latest_measurement else 0,
            'interface': latest_measurement.interface if latest_measurement else None,
        } if latest_measurement else None,
        'interfaces': interface_data,
        'time_range_hours': hours,
    })


@require_GET
def device_ip_bandwidth_api(request, device_id):
    """API endpoint to get per-IP bandwidth usage for a specific device"""
    device = get_object_or_404(NetworkDevice, id=device_id)
    
    # Parse parameters
    hours = int(request.GET.get('hours', 24))
    limit = int(request.GET.get('limit', 50))
    ip_range = request.GET.get('ip_range', None)
    view_type = request.GET.get('view', 'consumers')  # 'consumers', 'summary', 'trends'
    
    try:
        # Initialize Sophos monitoring service for firewall devices
        if device.device_type == NetworkDevice.TYPE_FIREWALL:
            from .services.sophos_service import SophosMonitoringService
            service = SophosMonitoringService(device)
            
            if view_type == 'consumers':
                data = service.get_top_bandwidth_consumers(limit=limit, time_period_hours=hours)
            elif view_type == 'summary':
                data = service.get_bandwidth_summary(time_period_hours=hours)
            elif view_type == 'trends':
                data = service.get_bandwidth_trends(hours=hours)
            elif view_type == 'range':
                data = service.get_bandwidth_by_ip_range(ip_range=ip_range, time_period_hours=hours)
            else:
                data = service.get_top_bandwidth_consumers(limit=limit, time_period_hours=hours)
        else:
            # For non-firewall devices, return empty data
            data = []
            
        return JsonResponse({
            'device': {
                'id': device.id,
                'name': device.name,
                'ip_address': device.ip_address,
                'device_type': device.device_type,
                'device_type_display': device.get_device_type_display(),
            },
            'view_type': view_type,
            'time_range_hours': hours,
            'data': data,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting IP bandwidth data for device {device_id}: {e}")
        return JsonResponse({
            'error': str(e),
            'device': device.id,
            'data': []
        }, status=500)


@require_GET
def bandwidth_summary_api(request):
    """API endpoint to get bandwidth summary for all devices"""
    hours = int(request.GET.get('hours', 1))  # Default to last hour
    since = timezone.now() - timedelta(hours=hours)
    
    # Get latest measurement for each device
    latest_measurements = {}
    measurements = DeviceBandwidthMeasurement.objects.filter(
        timestamp__gte=since
    ).select_related('device').order_by('device', '-timestamp')
    
    # Group by device and keep only latest
    for measurement in measurements:
        device_id = measurement.device.id
        if device_id not in latest_measurements:
            latest_measurements[device_id] = measurement
    
    # Create summary
    devices = []
    total_bandwidth = 0
    
    for device_id, measurement in latest_measurements.items():
        device_data = {
            'id': measurement.device.id,
            'name': measurement.device.name,
            'ip_address': measurement.device.ip_address,
            'device_type': measurement.device.device_type,
            'device_type_display': measurement.device.get_device_type_display(),
            'total_mbps': measurement.total_mbps,
            'mbps_in': measurement.mbps_in,
            'mbps_out': measurement.mbps_out,
            'total_pps': measurement.total_pps,
            'interface': measurement.interface,
            'timestamp': measurement.timestamp.isoformat(),
        }
        devices.append(device_data)
        total_bandwidth += measurement.total_mbps
    
    # Sort by total bandwidth
    devices.sort(key=lambda x: x['total_mbps'], reverse=True)
    
    return JsonResponse({
        'devices': devices,
        'summary': {
            'total_devices': len(devices),
            'total_bandwidth_mbps': total_bandwidth,
            'active_devices': len([d for d in devices if d['total_mbps'] > 0.1]),
            'time_range_hours': hours,
        },
        'top_consumers': devices[:10]  # Top 10 consumers
    })


@csrf_exempt
@require_http_methods(["POST"])
def start_bandwidth_monitoring_api(request):
    """API endpoint to start bandwidth monitoring for a device"""
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        interval = data.get('interval', 60)
        method = data.get('method', 'auto')
        snmp_community = data.get('snmp_community', 'public')
        
        if device_id:
            device = get_object_or_404(NetworkDevice, id=device_id)
            command = f"python manage.py monitor_bandwidth --device-ip {device.ip_address} --interval {interval} --method {method} --snmp-community {snmp_community} --duration 60"
        else:
            command = f"python manage.py monitor_bandwidth --interval {interval} --method {method} --snmp-community {snmp_community} --duration 60"
        
        # In a real implementation, you would run this as a background task
        # For now, just return success
        return JsonResponse({
            'success': True,
            'message': 'Bandwidth monitoring started',
            'command': command,
            'note': 'This would run as a background task in production'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid_json"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)



@require_GET
def current_connection_api(request):
    """Detect the user's current network device connection"""
    try:
        # Get client IP address with better handling of proxies
        client_ip = None
        
        # Check for manual override for testing (only in development)
        manual_ip = request.GET.get('manual_ip')
        if manual_ip and True:  # Always allow manual override for testing
            client_ip = manual_ip.strip()
        else:
            # Check various headers for the real client IP
            ip_headers = [
                'HTTP_X_FORWARDED_FOR',
                'HTTP_X_REAL_IP', 
                'HTTP_CLIENT_IP',
                'HTTP_X_CLUSTER_CLIENT_IP',
                'REMOTE_ADDR'
            ]
            
            for header in ip_headers:
                ip = request.META.get(header)
                if ip:
                    if header == 'HTTP_X_FORWARDED_FOR':
                        # X-Forwarded-For can contain multiple IPs, take the first one
                        client_ip = ip.split(',')[0].strip()
                    else:
                        client_ip = ip.strip()
                    break
        
        if not client_ip:
            client_ip = 'unknown'
        
        # Try to find a matching network device
        matching_device = None
        devices = NetworkDevice.objects.filter(enabled=True)
        
        # First, try exact IP match
        for device in devices:
            if device.ip_address == client_ip:
                matching_device = device
                break
        
        # If no exact match, try subnet match (but be more restrictive)
        if not matching_device and client_ip != 'unknown':
            for device in devices:
                if device.ip_address and _is_same_subnet(client_ip, device.ip_address):
                    # Only consider it a match if it's a reasonable network device
                    # (not just any device in the same subnet)
                    if device.device_type in ['ROUTER', 'FIREWALL', 'SWITCH', 'ACCESS_POINT']:
                        matching_device = device
                        break
        
        if matching_device:
            return JsonResponse({
                'success': True,
                'current_device': {
                    'id': matching_device.id,
                    'name': matching_device.name,
                    'ip_address': matching_device.ip_address,
                    'device_type': matching_device.device_type,
                    'device_type_display': matching_device.get_device_type_display(),
                    'is_active': matching_device.is_active,
                    'mac_address': matching_device.mac_address,
                    'vendor': matching_device.vendor,
                    'hostname': matching_device.hostname,
                },
                'client_ip': client_ip,
                'connection_type': 'direct' if matching_device.ip_address == client_ip else 'same_subnet',
                'debug_info': {
                    'all_headers_checked': ip_headers if not manual_ip else ['manual_override'],
                    'device_count': devices.count(),
                    'exact_match': matching_device.ip_address == client_ip,
                    'manual_override_used': bool(manual_ip)
                }
            })
        else:
            return JsonResponse({
                'success': True,
                'current_device': None,
                'client_ip': client_ip,
                'message': 'No matching device found for current connection',
                'debug_info': {
                    'all_headers_checked': ip_headers if not manual_ip else ['manual_override'],
                    'device_count': devices.count(),
                    'available_ips': [d.ip_address for d in devices if d.ip_address],
                    'manual_override_used': bool(manual_ip)
                }
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'client_ip': request.META.get('REMOTE_ADDR', 'unknown')
        }, status=500)


def _is_same_subnet(ip1, ip2):
    """Check if two IPs are in the same subnet (simple /24 check)"""
    try:
        import ipaddress
        addr1 = ipaddress.IPv4Address(ip1)
        addr2 = ipaddress.IPv4Address(ip2)
        
        # Simple /24 subnet check
        return (int(addr1) // 256) == (int(addr2) // 256)
    except (ValueError, ipaddress.AddressValueError):
        return False


@require_GET
def network_diagram_api(request):
    """API endpoint for network topology diagram with VLAN-based hierarchical structure"""
    try:
        devices = NetworkDevice.objects.filter(enabled=True).order_by("name")
        
        if not devices:
            return JsonResponse({
                'success': False,
                'error': 'No network devices found'
            })
        
        # Find core firewall (Sophos XGS)
        core_firewall = devices.filter(device_type='FIREWALL').first()
        if not core_firewall:
            return JsonResponse({
                'success': False,
                'error': 'No firewall found for network topology'
            })
        
        # Define VLAN structure based on IP ranges
        vlan_segments = {
            'Admin VLAN': {
                'subnet': '192.168.1.0/24',
                'color': '#ef4444',  # Red
                'devices': []
            },
            'Faculty VLAN': {
                'subnet': '192.168.2.0/24', 
                'color': '#3b82f6',  # Blue
                'devices': []
            },
            'Student VLAN': {
                'subnet': '192.168.3.0/24',
                'color': '#10b981',  # Green
                'devices': []
            },
            'Servers VLAN': {
                'subnet': '192.168.4.0/24',
                'color': '#f59e0b',  # Orange
                'devices': []
            }
        }
        
        # Find core switch
        core_switch = devices.filter(device_type__in=['SWITCH', 'ROUTER']).first()
        
        # Group devices by VLAN based on IP address
        for device in devices:
            if device.ip_address and device.id != core_firewall.id:
                ip_parts = device.ip_address.split('.')
                if len(ip_parts) >= 3:
                    subnet_third_octet = ip_parts[2]
                    subnet_fourth_octet = ip_parts[3] if len(ip_parts) > 3 else ''
                    
                    # Handle 192.168.253.x subnet (management/infrastructure)
                    if subnet_third_octet == '253':
                        # This is the management subnet - create a special category
                        if 'Infrastructure VLAN' not in vlan_segments:
                            vlan_segments['Infrastructure VLAN'] = {
                                'subnet': '192.168.253.0/24',
                                'color': '#f59e0b',  # Orange
                                'devices': []
                            }
                        vlan_segments['Infrastructure VLAN']['devices'].append(device)
                    elif subnet_third_octet == '1':
                        vlan_segments['Admin VLAN']['devices'].append(device)
                    elif subnet_third_octet == '2':
                        vlan_segments['Faculty VLAN']['devices'].append(device)
                    elif subnet_third_octet == '3':
                        vlan_segments['Student VLAN']['devices'].append(device)
                    elif subnet_third_octet == '4':
                        vlan_segments['Servers VLAN']['devices'].append(device)
                    else:
                        # Default to Admin VLAN for unknown subnets
                        vlan_segments['Admin VLAN']['devices'].append(device)
        
        # Build diagram data structure with hierarchical VLAN layout
        nodes = []
        edges = []
        
        # Canvas dimensions with more space for grid layout
        canvas_width = 1400
        canvas_height = 1000
        
        # Level positions with more spacing
        internet_y = 50
        firewall_y = 150
        core_switch_y = 300
        vlan_y = 500
        device_y = 700
        
        # Add Internet node at top
        nodes.append({
            'id': 'internet',
            'name': 'Internet',
            'ip': '0.0.0.0',
            'type': 'internet',
            'device_type': 'INTERNET',
            'is_active': True,
            'level': 0,
            'x': canvas_width // 2,
            'y': internet_y,
            'size': 25,
            'subnet': 'internet',
            'mac_address': '',
            'vendor': 'Internet'
        })
        
        # Add Sophos XGS Firewall
        nodes.append({
            'id': f'firewall_{core_firewall.id}',
            'name': f'Sophos XGS ({core_firewall.name})',
            'ip': core_firewall.ip_address,
            'type': 'firewall',
            'device_type': core_firewall.device_type,
            'is_active': core_firewall.is_active,
            'level': 1,
            'x': canvas_width // 2,
            'y': firewall_y,
            'size': 30,
            'subnet': 'firewall',
            'mac_address': core_firewall.mac_address,
            'vendor': core_firewall.vendor
        })
        
        # Add Core Switch
        if core_switch:
            nodes.append({
                'id': f'core_switch_{core_switch.id}',
                'name': f'Core Switch ({core_switch.name})',
                'ip': core_switch.ip_address,
                'type': 'switch',
                'device_type': core_switch.device_type,
                'is_active': core_switch.is_active,
                'level': 2,
                'x': canvas_width // 2,
                'y': core_switch_y,
                'size': 25,
                'subnet': 'core',
                'mac_address': core_switch.mac_address,
                'vendor': core_switch.vendor
            })
            
            # Add edge from firewall to core switch
            edges.append({
                'from': f'firewall_{core_firewall.id}',
                'to': f'core_switch_{core_switch.id}',
                'type': 'network_connection',
                'subnet': 'core'
            })
        else:
            # Create a virtual core switch if none exists
            nodes.append({
                'id': 'virtual_core_switch',
                'name': 'Core Switch',
                'ip': '192.168.253.1',
                'type': 'switch',
                'device_type': 'SWITCH',
                'is_active': True,
                'level': 2,
                'x': canvas_width // 2,
                'y': core_switch_y,
                'size': 25,
                'subnet': 'core',
                'mac_address': '',
                'vendor': 'Virtual'
            })
            
            edges.append({
                'from': f'firewall_{core_firewall.id}',
                'to': 'virtual_core_switch',
                'type': 'network_connection',
                'subnet': 'core'
            })
        
        # Add VLAN segments
        vlan_width = canvas_width // (len(vlan_segments) + 1)
        core_switch_id = f'core_switch_{core_switch.id}' if core_switch else 'virtual_core_switch'
        
        for i, (vlan_name, vlan_info) in enumerate(vlan_segments.items()):
            vlan_x = vlan_width * (i + 1)
            
            # Add VLAN segment node
            nodes.append({
                'id': f'vlan_{vlan_name.lower().replace(" ", "_")}',
                'name': vlan_name,
                'ip': vlan_info['subnet'],
                'type': 'vlan',
                'device_type': 'VLAN',
                'is_active': True,
                'level': 3,
                'x': vlan_x,
                'y': vlan_y,
                'size': 20,
                'subnet': vlan_info['subnet'],
                'mac_address': '',
                'vendor': 'VLAN Segment',
                'color': vlan_info['color']
            })
            
            # Add edge from core switch to VLAN
            edges.append({
                'from': core_switch_id,
                'to': f'vlan_{vlan_name.lower().replace(" ", "_")}',
                'type': 'vlan_connection',
                'subnet': vlan_info['subnet']
            })
            
            # Add devices in this VLAN with improved spacing
            vlan_devices = vlan_info['devices']
            if vlan_devices:
                # Use better spacing algorithm to prevent overlapping
                max_devices_per_row = 8  # Limit devices per row
                device_spacing = 80
                row_spacing = 100
                
                # Calculate grid layout
                num_rows = (len(vlan_devices) + max_devices_per_row - 1) // max_devices_per_row
                total_width = min(len(vlan_devices), max_devices_per_row) * device_spacing
                device_start_x = max(50, vlan_x - total_width // 2)
                
                for j, device in enumerate(vlan_devices[:20]):  # Increased limit but still reasonable
                    row = j // max_devices_per_row
                    col = j % max_devices_per_row
                    
                    device_x = device_start_x + (col * device_spacing)
                    device_y = device_y + (row * row_spacing)
                    
                    device_node = {
                        'id': f'device_{device.id}',
                        'name': device.name,
                        'ip': device.ip_address,
                        'type': device.device_type.lower(),
                        'device_type': device.device_type,
                        'is_active': device.is_active,
                        'level': 4,
                        'x': device_x,
                        'y': device_y,
                        'size': 12,
                        'subnet': vlan_info['subnet'],
                        'mac_address': device.mac_address,
                        'vendor': device.vendor,
                        'color': vlan_info['color']
                    }
                    nodes.append(device_node)
                    
                    # Add edge from VLAN to device
                    edges.append({
                        'from': f'vlan_{vlan_name.lower().replace(" ", "_")}',
                        'to': f'device_{device.id}',
                        'type': 'device_connection',
                        'subnet': vlan_info['subnet']
                    })
        
        # Add edge from Internet to Firewall
        edges.append({
            'from': 'internet',
            'to': f'firewall_{core_firewall.id}',
            'type': 'internet_connection',
            'subnet': 'internet'
        })
        
        return JsonResponse({
            'success': True,
            'diagram_data': {
                'nodes': nodes,
                'edges': edges,
                'total_devices': len(devices),
                'total_segments': len(vlan_segments),
                'core_firewall': {
                    'name': core_firewall.name,
                    'ip': core_firewall.ip_address
                },
                'core_switch': {
                    'name': core_switch.name if core_switch else 'Virtual Core Switch',
                    'ip': core_switch.ip_address if core_switch else '192.168.253.1'
                },
                'vlan_segments': list(vlan_segments.keys()),
                'layout_type': 'vlan_hierarchical'
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
def _get_subnet(ip_address, prefix_length=24):
    """Get subnet for an IP address"""
    try:
        import ipaddress
        network = ipaddress.IPv4Network(f"{ip_address}/{prefix_length}", strict=False)
        return str(network.network_address)
    except (ValueError, ipaddress.AddressValueError):
        return "unknown"


@require_GET
def bandwidth_report_csv(request, device_id):
    """Generate CSV report for bandwidth usage"""
    device = get_object_or_404(NetworkDevice, id=device_id)
    
    # Parse parameters
    hours = int(request.GET.get('hours', 24))
    view_type = request.GET.get('view', 'consumers')
    
    try:
        report_service = BandwidthReportService()
        return report_service.generate_csv_report(device_id, hours, view_type)
    except Exception as e:
        logger.error(f"Error generating CSV report: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@require_GET
def bandwidth_report_pdf(request, device_id):
    """Generate PDF report for bandwidth usage"""
    device = get_object_or_404(NetworkDevice, id=device_id)
    
    # Parse parameters
    hours = int(request.GET.get('hours', 24))
    view_type = request.GET.get('view', 'consumers')
    
    try:
        report_service = BandwidthReportService()
        return report_service.generate_pdf_report(device_id, hours, view_type)
    except Exception as e:
        logger.error(f"Error generating PDF report: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@require_GET
def cctv_dashboard(request):
    """CCTV camera dashboard view"""
    devices = CCTVDevice.objects.all().order_by('name')
    
    # Count devices by status
    online_count = devices.filter(status='online').count()
    offline_count = devices.filter(status='offline').count()
    unknown_count = devices.filter(status='unknown').count()
    
    context = {
        'devices': devices,
        'total_devices': devices.count(),
        'online_count': online_count,
        'offline_count': offline_count,
        'unknown_count': unknown_count,
        'active_nav': 'cctv',
    }
    
    return render(request, 'monitor/cctv_dashboard.html', context)


@require_http_methods(["GET", "POST"])
def import_cctv_xml(request):
    """Import CCTV devices from XML configuration"""
    if request.method == 'POST':
        xml_content = request.POST.get('xml_content', '')
        if xml_content:
            try:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(xml_content)
                
                imported_count = 0
                for device_elem in root.findall('Device'):
                    name = device_elem.get('name', '')
                    domain = device_elem.get('domain', '')
                    port = int(device_elem.get('port', '37777'))
                    username = device_elem.get('username', 'admin')
                    password = device_elem.get('password', 'admin123456')
                    protocol = device_elem.get('protocol', '1')
                    connect = device_elem.get('connect', '19')
                    
                    if name and domain:
                        # Create or update device
                        device, created = CCTVDevice.objects.update_or_create(
                            name=name,
                            defaults={
                                'domain': domain,
                                'port': port,
                                'username': username,
                                'password': password,
                                'protocol': protocol,
                                'connect': connect,
                            }
                        )
                        imported_count += 1
                
                return JsonResponse({
                    'success': True,
                    'message': f'Successfully imported {imported_count} devices'
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'XML parsing error: {str(e)}'
                })
        else:
            return JsonResponse({
                'success': False,
                'error': 'No XML content provided'
            })
    
    return render(request, 'monitor/cctv_import.html')


@require_http_methods(["POST"])
def check_cctv_status(request):
    """Check status of a specific CCTV device"""
    device_id = request.POST.get('device_id')
    if not device_id:
        return JsonResponse({
            'success': False,
            'error': 'Device ID is required'
        })
    
    try:
        device = CCTVDevice.objects.get(id=device_id)
        device.check_status()
        
        return JsonResponse({
            'success': True,
            'status': device.status,
            'last_checked': device.last_checked.strftime('%Y-%m-%d %H:%M:%S') if device.last_checked else None
        })
        
    except CCTVDevice.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Device not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@require_GET
def check_all_cctv_status(request):
    """Check status of all CCTV devices"""
    try:
        devices = CCTVDevice.objects.all()
        results = []
        
        for device in devices:
            device.check_status()
            results.append({
                'id': device.id,
                'name': device.name,
                'status': device.status,
                'last_checked': device.last_checked.strftime('%Y-%m-%d %H:%M:%S') if device.last_checked else None
            })
        
        return JsonResponse({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@require_GET
def cctv_camera_detail(request, device_id, camera_number):
    """Show detailed view of a specific camera"""
    device = get_object_or_404(CCTVDevice, id=device_id)
    
    # Validate camera number
    if camera_number < 1 or camera_number > device.camera_count:
        return JsonResponse({'error': 'Invalid camera number'}, status=404)
    
    context = {
        'device': device,
        'camera_number': camera_number,
        'camera_name': device.get_camera_name(camera_number),
        'rtsp_url': device.get_rtsp_url(camera_number),
    }
    
    return render(request, 'monitor/cctv_camera_detail.html', context)


@require_GET
def cctv_device_detail(request, device_id):
    """Show detailed view of a CCTV device with all cameras"""
    device = get_object_or_404(CCTVDevice, id=device_id)
    
    cameras = []
    for cam_num in device.get_camera_list():
        cameras.append({
            'number': cam_num,
            'name': device.get_camera_name(cam_num),
            'rtsp_url': device.get_rtsp_url(cam_num),
        })
    
    context = {
        'device': device,
        'cameras': cameras,
    }
    
    return render(request, 'monitor/cctv_device_detail.html', context)


@require_GET
def cctv_live_stream(request, device_id, camera_number):
    """Get live MJPEG stream from camera"""
    from .video_service import VideoStreamingService
    
    stream_service = VideoStreamingService()
    return stream_service.stream_mjpeg_response(device_id, camera_number)


@require_GET
def cctv_snapshot(request, device_id, camera_number):
    """Get live snapshot from camera"""
    from .video_service import VideoStreamingService
    
    stream_service = VideoStreamingService()
    snapshot = stream_service.get_live_snapshot(device_id, camera_number)
    
    if snapshot:
        return JsonResponse({'success': True, 'snapshot': snapshot})
    else:
        return JsonResponse({'success': False, 'error': 'Failed to get snapshot'})


@require_GET
def cctv_test_connection(request, device_id, camera_number):
    """Test connection to specific camera"""
    from .video_service import VideoStreamingService
    
    stream_service = VideoStreamingService()
    connected = stream_service.test_camera_connection(device_id, camera_number)
    
    return JsonResponse({
        'success': connected,
        'message': 'Connection successful' if connected else 'Connection failed'
    })


@require_POST
def dmss_login(request):
    """DMSS cloud login"""
    from .dmss_integration import authenticate_dmss, sync_dmss_devices_to_db
    
    username = request.POST.get('username')
    password = request.POST.get('password')
    
    if not username or not password:
        return JsonResponse({'success': False, 'error': 'Username and password required'})
    
    try:
        client, message = authenticate_dmss(username, password)
        
        if client:
            # Sync devices to database
            sync_success, sync_message = sync_dmss_devices_to_db()
            
            return JsonResponse({
                'success': True,
                'message': f'Login successful. {sync_message}',
                'devices_count': len(client.devices)
            })
        else:
            return JsonResponse({'success': False, 'error': message})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST
def dmss_logout(request):
    """DMSS cloud logout"""
    from .dmss_integration import get_dmss_client
    
    try:
        client = get_dmss_client()
        success, message = client.logout()
        
        return JsonResponse({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_GET
def dmss_status(request):
    """Get DMSS login status"""
    from .dmss_integration import get_dmss_client
    
    try:
        client = get_dmss_client()
        
        if client.is_logged_in():
            devices, message = client.get_device_list()
            
            return JsonResponse({
                'logged_in': True,
                'username': client.username,
                'devices_count': len(devices),
                'message': message
            })
        else:
            return JsonResponse({
                'logged_in': False,
                'message': 'Not logged in'
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_GET
def dmss_devices(request):
    """Get DMSS devices"""
    from .dmss_integration import get_dmss_devices
    
    try:
        devices, message = get_dmss_devices()
        
        return JsonResponse({
            'success': True,
            'devices': devices,
            'message': message
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_GET
def dmss_device_stream(request, device_id, channel=0):
    """Get live stream from DMSS device"""
    from .dmss_integration import get_dmss_client
    
    try:
        client = get_dmss_client()
        
        if not client.is_logged_in():
            return JsonResponse({'success': False, 'error': 'Not logged in'})
        
        stream_url, message = client.get_live_stream_url(device_id, channel)
        
        if stream_url:
            return JsonResponse({
                'success': True,
                'stream_url': stream_url,
                'message': message
            })
        else:
            return JsonResponse({'success': False, 'error': message})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_GET
def dmss_test_page(request):
    """DMSS test page with simple login form"""
    return render(request, 'monitor/dmss_test.html')

@require_GET
def p2p_camera_access(request):
    """P2P camera access page"""
    return render(request, 'monitor/p2p_camera_access.html')

@require_POST
def p2p_connect(request):
    """Connect to camera via P2P"""
    from .dahua_p2p import DahuaP2PClient
    
    try:
        serial_number = request.POST.get('serial_number')
        username = request.POST.get('username', 'admin')
        password = request.POST.get('password', 'admin123456')
        
        if not serial_number:
            return JsonResponse({'success': False, 'error': 'Serial number is required'})
        
        # Initialize P2P client
        client = DahuaP2PClient(serial_number, username, password)
        
        # Test P2P connection
        p2p_server = client.probe_p2p_server()
        
        if not p2p_server:
            return JsonResponse({'success': False, 'error': 'No P2P servers available'})
        
        # Try to establish connection
        connection_result = client.establish_connection()
        
        if connection_result:
            camera_info = {
                'serial_number': serial_number,
                'status': 'Connected',
                'connection_type': 'P2P',
                'device_ip': client.device_ip,
                'device_port': client.device_port,
                'p2p_server': p2p_server
            }
            
            return JsonResponse({
                'success': True,
                'camera_info': camera_info,
                'message': f'Connected to camera {serial_number} via P2P'
            })
        else:
            return JsonResponse({'success': False, 'error': 'Failed to establish P2P connection'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_POST
def p2p_stream(request):
    """Get P2P stream URL"""
    from .dahua_p2p import DahuaP2PClient
    
    try:
        serial_number = request.POST.get('serial_number')
        username = request.POST.get('username', 'admin')
        password = request.POST.get('password', 'admin123456')
        stream_type = request.POST.get('stream_type', 'main')
        
        if not serial_number:
            return JsonResponse({'success': False, 'error': 'Serial number is required'})
        
        # Initialize P2P client
        client = DahuaP2PClient(serial_number, username, password)
        
        # Get stream URL
        stream_url = client.get_rtsp_url(stream_type)
        
        if stream_url:
            return JsonResponse({
                'success': True,
                'stream_url': stream_url,
                'message': f'Stream URL generated for {serial_number}'
            })
        else:
            return JsonResponse({'success': False, 'error': 'Failed to generate stream URL'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_POST
def p2p_snapshot(request):
    """Get P2P snapshot"""
    from .dahua_p2p import DahuaP2PClient
    
    try:
        serial_number = request.POST.get('serial_number')
        username = request.POST.get('username', 'admin')
        password = request.POST.get('password', 'admin123456')
        
        if not serial_number:
            return JsonResponse({'success': False, 'error': 'Serial number is required'})
        
        # Initialize P2P client
        client = DahuaP2PClient(serial_number, username, password)
        
        # Get snapshot
        snapshot_data = client.get_snapshot()
        
        if snapshot_data:
            # Convert to base64 for web display
            import base64
            snapshot_b64 = base64.b64encode(snapshot_data).decode('utf-8')
            
            return JsonResponse({
                'success': True,
                'snapshot': f"data:image/jpeg;base64,{snapshot_b64}",
                'message': f'Snapshot captured from {serial_number}'
            })
        else:
            return JsonResponse({'success': False, 'error': 'Failed to capture snapshot'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST
@csrf_exempt
def update_device_type_api(request, device_id):
    """API endpoint to update device type"""
    try:
        device = get_object_or_404(NetworkDevice, id=device_id)
        new_device_type = request.POST.get('device_type')
        
        if not new_device_type:
            return JsonResponse({'success': False, 'error': 'Device type is required'})
        
        # Validate device type
        valid_types = [choice[0] for choice in NetworkDevice.TYPE_CHOICES]
        if new_device_type not in valid_types:
            return JsonResponse({'success': False, 'error': 'Invalid device type'})
        
        # Update device type
        old_device_type = device.device_type
        device.device_type = new_device_type
        device.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Device type updated from {old_device_type} to {new_device_type}',
            'old_device_type': old_device_type,
            'new_device_type': new_device_type,
            'device_type_display': device.get_device_type_display()
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# Network Device Report Generation

@require_GET
def network_device_reports(request):
    """Generate network device reports (CSV and PDF) categorized by network and ordered by device type"""
    
    # Get filter parameters
    network_filter = request.GET.get('network', '')
    device_type_filter = request.GET.get('device_type', '')
    active_filter = request.GET.get('active', '')
    
    # Start with base queryset
    devices = NetworkDevice.objects.all()
    
    # Apply filters
    if network_filter:
        devices = devices.filter(network=network_filter)
    if device_type_filter:
        devices = devices.filter(device_type=device_type_filter)
    if active_filter:
        devices = devices.filter(is_active=(active_filter.lower() == 'true'))
    
    # Order by network, then device type, then name
    devices = devices.order_by('network', 'device_type', 'name')
    
    # Get available networks for filter dropdown
    available_networks = NetworkDevice.objects.filter(
        network__isnull=False
    ).values_list('network', flat=True).distinct().order_by('network')
    
    context = {
        'devices': devices,
        'available_networks': available_networks,
        'current_filters': {
            'network': network_filter,
            'device_type': device_type_filter,
            'active': active_filter,
        },
        'total_devices': devices.count(),
        'total_networks': available_networks.count(),
    }
    
    return render(request, 'monitor/network_device_reports.html', context)


@require_GET
def network_device_report_csv(request):
    """Generate CSV report for network devices"""
    
    # Get filter parameters
    network_filter = request.GET.get('network', '')
    device_type_filter = request.GET.get('device_type', '')
    active_filter = request.GET.get('active', '')
    
    # Start with base queryset
    devices = NetworkDevice.objects.all()
    
    # Apply filters
    if network_filter:
        devices = devices.filter(network=network_filter)
    if device_type_filter:
        devices = devices.filter(device_type=device_type_filter)
    if active_filter:
        devices = devices.filter(is_active=(active_filter.lower() == 'true'))
    
    # Order by network, then device type, then name
    devices = devices.order_by('network', 'device_type', 'name')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="network_devices_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # Header
    writer.writerow([
        'Network', 'Device Name', 'Device Type', 'IP Address', 'MAC Address', 
        'Vendor', 'Hostname', 'Status', 'Auto Discovered', 
        'First Seen', 'Last Seen', 'Notes'
    ])
    
    # Data rows
    for device in devices:
        writer.writerow([
            device.network or 'Unknown Network',
            device.name,
            device.get_device_type_display(),
            device.ip_address,
            device.mac_address or '',
            device.vendor or '',
            device.hostname or '',
            'Active' if device.is_active else 'Inactive',
            'Yes' if device.auto_discovered else 'No',
            device.first_seen.strftime('%Y-%m-%d %H:%M') if device.first_seen else '',
            device.last_seen.strftime('%Y-%m-%d %H:%M') if device.last_seen else '',
            device.notes or ''
        ])
    
    return response


@require_GET
def network_device_report_pdf(request):
    """Generate PDF report for network devices"""
    
    # Get filter parameters
    network_filter = request.GET.get('network', '')
    device_type_filter = request.GET.get('device_type', '')
    active_filter = request.GET.get('active', '')
    
    # Start with base queryset
    devices = NetworkDevice.objects.all()
    
    # Apply filters
    if network_filter:
        devices = devices.filter(network=network_filter)
    if device_type_filter:
        devices = devices.filter(device_type=device_type_filter)
    if active_filter:
        devices = devices.filter(is_active=(active_filter.lower() == 'true'))
    
    # Order by network, then device type, then name
    devices = devices.order_by('network', 'device_type', 'name')
    
    # Create PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="network_devices_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
    
    # PDF generation
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.darkblue
    )
    
    # Create PDF content
    from io import BytesIO
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []
    
    # Title
    title = Paragraph("Network Devices Report", title_style)
    story.append(title)
    
    # Report generation time and filters
    timestamp = Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal'])
    story.append(timestamp)
    
    # Add filters if any
    filter_text = []
    if network_filter:
        filter_text.append(f"Network: {network_filter}")
    if device_type_filter:
        filter_text.append(f"Device Type: {device_type_filter}")
    if active_filter:
        filter_text.append(f"Status: {'Active' if active_filter.lower() == 'true' else 'Inactive'}")
    
    if filter_text:
        story.append(Paragraph(f"Filters: {', '.join(filter_text)}", styles['Normal']))
        story.append(Spacer(1, 20))
    
    story.append(Spacer(1, 20))
    
    # Group devices by network
    devices_by_network = {}
    for device in devices:
        network = device.network or 'Unknown Network'
        if network not in devices_by_network:
            devices_by_network[network] = []
        devices_by_network[network].append(device)
    
    total_devices = sum(len(devices) for devices in devices_by_network.values())
    
    # Summary statistics
    summary_data = [
        ['Total Networks:', str(len(devices_by_network))],
        ['Total Devices:', str(total_devices)],
    ]
    
    # Device type summary
    device_type_counts = {}
    for devices in devices_by_network.values():
        for device in devices:
            device_type = device.get_device_type_display()
            device_type_counts[device_type] = device_type_counts.get(device_type, 0) + 1
    
    for device_type, count in sorted(device_type_counts.items()):
        summary_data.append([f'{device_type}:', str(count)])
    
    summary_table = Table(summary_data, colWidths=[2*inch, 1*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(Paragraph("Summary Statistics", heading_style))
    story.append(summary_table)
    story.append(Spacer(1, 30))
    
    # Detailed devices by network
    for network, network_devices in devices_by_network.items():
        # Network heading
        story.append(Paragraph(f"Network: {network}", heading_style))
        story.append(Spacer(1, 12))
        
        # Device table
        table_data = [['Device Name', 'Type', 'IP Address', 'MAC Address', 'Vendor', 'Status']]
        
        for device in network_devices:
            table_data.append([
                device.name,
                device.get_device_type_display(),
                device.ip_address,
                device.mac_address or 'N/A',
                device.vendor or 'N/A',
                'Active' if device.is_active else 'Inactive'
            ])
        
        # Create table
        table = Table(table_data, colWidths=[1.8*inch, 1.2*inch, 1.2*inch, 1.3*inch, 1.2*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 20))
    
    # Build PDF
    doc.build(story)
    pdf_value = buffer.getvalue()
    buffer.close()
    
    response.write(pdf_value)
    return response


@require_GET
def dmss_device_snapshot(request, device_id, channel=0):
    """Get snapshot from DMSS device"""
    from .dmss_integration import get_dmss_client
    
    try:
        client = get_dmss_client()
        
        if not client.is_logged_in():
            return JsonResponse({'success': False, 'error': 'Not logged in'})
        
        snapshot_data, message = client.get_device_snapshot(device_id, channel)
        
        if snapshot_data:
            # Convert to base64 for web display
            import base64
            snapshot_b64 = base64.b64encode(snapshot_data).decode('utf-8')
            
            return JsonResponse({
                'success': True,
                'snapshot': f"data:image/jpeg;base64,{snapshot_b64}",
                'message': message
            })
        else:
            return JsonResponse({'success': False, 'error': message})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def isp_speed_test_api(request):
    """API endpoint to run speed test for a specific ISP"""
    try:
        data = json.loads(request.body)
        isp_id = data.get('isp_id')
        
        if not isp_id:
            return JsonResponse({'success': False, 'error': 'ISP ID is required'})
        
        # Get ISP connection
        isp = get_object_or_404(ISPConnection, id=isp_id)
        
        # Run speed test
        from monitor.isp_monitor import ISPMonitor
        monitor = ISPMonitor(isp)
        
        # Test bandwidth specifically
        bandwidth = monitor.test_bandwidth()
        
        if bandwidth is not None:
            # Update the bandwidth metric
            from monitor.models import ISPMetric
            from django.utils import timezone
            
            # Save the new bandwidth metric
            ISPMetric.objects.create(
                connection=isp,
                metric_name='bandwidth_mbps',
                value=bandwidth,
                unit='Mbps',
                timestamp=timezone.now()
            )
            
            # Update the ISP's last_checked timestamp
            isp.last_checked = timezone.now()
            isp.save(update_fields=['last_checked'])
            
            return JsonResponse({
                'success': True,
                'bandwidth_mbps': bandwidth,
                'message': f'Speed test completed for {isp.name}'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Speed test failed - unable to measure bandwidth'
            })
            
    except ISPConnection.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'ISP not found'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def dashboard_new_test(request):
    """
    Temporary view to test the new dashboard layout.
    """
    from .models import Server
    from collections import defaultdict
    
    servers = Server.objects.filter(enabled=True).order_by('server_type', 'name')
    servers_by_type = defaultdict(list)
    for s in servers:
        # Use display name for grouping
        display_name = s.get_server_type_display()
        servers_by_type[display_name].append(s)
    
    return render(request, 'monitor/dashboard_new.html', {
        'servers_by_type': dict(servers_by_type)
    })


from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response as DRFResponse
from rest_framework.permissions import IsAuthenticated, AllowAny

@api_view(['GET'])
@permission_classes([AllowAny])
def server_detailed_metrics_api(request, server_id):
    """
    API endpoint to get detailed real-time and historical metrics for a specific server.
    """
    from .models import Server
    from .services.metrics_monitor_service import MetricsMonitorService
    
    server = get_object_or_404(Server, id=server_id)
    monitor = MetricsMonitorService()
    
    # 1. Get Real-time Metrics (CPU, RAM, Disk, SSL, Directory)
    metrics_data = monitor.get_comprehensive_metrics(server.ip_address, server=server)
    logger.info(f"server_detailed_metrics_api for {server.name} ({server.id}) - metrics_data: {json.dumps(metrics_data, indent=2)}")
    
    # 2. Get Historical Data (Last 24 hours)
    historical = monitor.get_performance_trend(server, hours=24)
    
    # 3. Get SSL Certificates from database
    from .models import SSLCertificate
    db_certs = list(SSLCertificate.objects.filter(server=server).values(
        'name', 'domain', 'issuer', 'expires_at', 'days_until_expiry', 'is_valid', 'last_checked'
    ))
    
    # 4. Service Status (Example check)
    services = [
        {'name': 'SSH', 'status': 'up' if server.last_status == 'UP' else 'down'},
        {'name': 'HTTP', 'status': 'up' if server.last_http_ok else 'down'},
    ]
    if server.last_db_connect_ok is not None:
        services.append({'name': 'Database', 'status': 'up' if server.last_db_connect_ok else 'down'})

    return DRFResponse({
        'success': True,
        'server_id': server.id,
        'server_name': server.name,
        'ip_address': server.ip_address,
        'server': {
            'id': server.id,
            'name': server.name,
            'ip_address': server.ip_address,
            'watch_directory': server.watch_directory,
            'latest_folder_name': server.latest_folder_name,
            'latest_folder_files': server.latest_folder_files,
            'latest_folder_size_mb': server.latest_folder_size_mb,
            'latest_folder_created': server.latest_folder_created.isoformat() if server.latest_folder_created else None,
        },
        'monitored_directories': server.monitored_directories,
        'metrics': metrics_data.get('current', {}),
        'historical': historical,
        'ssl': metrics_data.get('current', {}).get('ssl', {}),
        'db_ssl': db_certs,
        'directory_watch': metrics_data.get('current', {}).get('directory_watch', []),
        'services': services,
        'timestamp': timezone.now().isoformat()
    })


@require_POST
@csrf_exempt
def update_server_directories(request, server_id):
    """
    API endpoint to update monitored directories for a server.
    """
    from .models import Server
    import json
    
    server = get_object_or_404(Server, id=server_id)
    try:
        data = json.loads(request.body)
        directories = data.get('directories', '')
        
        server.monitored_directories = directories
        server.save(update_fields=['monitored_directories'])
        
        # Clear cache to force fresh collection with new paths
        from django.core.cache import cache
        cache_key = f'device_metrics_{server.ip_address}'
        cache.delete(cache_key)
        
        return JsonResponse({
            'success': True,
            'message': 'Monitored directories updated successfully',
            'directories': server.monitored_directories
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def dtr_monitoring_dashboard(request):
    """DTR Biometric Monitoring Dashboard"""
    return render(request, 'monitor/dtr_monitoring_dashboard.html')

