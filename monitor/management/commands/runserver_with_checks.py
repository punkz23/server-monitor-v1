import os
import threading
import time

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from daphne.management.commands.runserver import Command as RunserverCommand
from django.db import transaction
from django.utils import timezone

from monitor.checks import check_server
from monitor.alerts import evaluate_alerts_for_server
from monitor.models import CheckResult, Server


class Command(RunserverCommand):
    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument("--timeout", type=float, default=3.0)
        parser.add_argument("--limit", type=int, default=0)
        parser.add_argument("--interval", type=float, default=1.0)

    def inner_run(self, *args, **options):
        stop_event = threading.Event()

        def checker_loop():
            timeout = float(options["timeout"])
            limit = int(options["limit"])
            interval = float(options["interval"])
            interval = max(0.1, interval)

            channel_layer = get_channel_layer()

            while not stop_event.is_set():
                start = time.perf_counter()

                qs = Server.objects.filter(enabled=True).order_by("-pinned", "name")
                if limit and limit > 0:
                    qs = qs[:limit]

                now = timezone.now()

                for server in qs:
                    outcome = check_server(
                        ip=server.ip_address,
                        port=server.port,
                        do_http_check=server.http_check,
                        use_https=server.use_https,
                        path=server.path,
                        timeout_seconds=timeout,
                    )

                    status = Server.STATUS_UP if outcome.tcp_ok else Server.STATUS_DOWN
                    latency_ms = (
                        outcome.http_latency_ms
                        if outcome.http_ok
                        else outcome.tcp_latency_ms
                    )

                    with transaction.atomic():
                        CheckResult.objects.create(
                            server=server,
                            status=status,
                            http_ok=outcome.http_ok,
                            latency_ms=latency_ms,
                            http_status_code=outcome.http_status_code,
                            error=outcome.error,
                        )

                        server.last_status = status
                        server.last_checked = now
                        server.last_http_ok = outcome.http_ok
                        server.last_latency_ms = latency_ms
                        server.last_http_status_code = outcome.http_status_code
                        server.last_error = outcome.error
                        server.save(
                            update_fields=[
                                "last_status",
                                "last_http_ok",
                                "last_checked",
                                "last_latency_ms",
                                "last_http_status_code",
                                "last_error",
                                "updated_at",
                            ]
                        )

                    evaluate_alerts_for_server(server=server, now=now, channel_layer=channel_layer)

                    if channel_layer is not None:
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

                elapsed = time.perf_counter() - start
                sleep_for = interval - elapsed
                if sleep_for > 0:
                    stop_event.wait(timeout=sleep_for)

        t = None
        try:
            if options.get("use_reloader") and (os.environ.get("RUN_MAIN") != "true"):
                return super().inner_run(*args, **options)

            self.stdout.write(self.style.WARNING("Starting background checks thread..."))
            t = threading.Thread(target=checker_loop, daemon=True)
            t.start()
            return super().inner_run(*args, **options)
        finally:
            stop_event.set()
            if t is not None:
                t.join(timeout=2.0)
