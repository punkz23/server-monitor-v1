from __future__ import annotations

import socket
import ssl
import time
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class CheckOutcome:
    tcp_ok: bool
    tcp_latency_ms: int | None
    http_ok: bool | None
    http_latency_ms: int | None
    http_status_code: int | None
    error: str


def tcp_check(ip: str, port: int, timeout_seconds: float) -> int:
    start = time.perf_counter()
    with socket.create_connection((ip, port), timeout=timeout_seconds):
        pass
    end = time.perf_counter()
    return int(round((end - start) * 1000))


def http_check(
    *,
    ip: str,
    port: int,
    use_https: bool,
    path: str,
    timeout_seconds: float,
) -> tuple[int, int]:
    scheme = "https" if use_https else "http"
    normalized_path = path if path.startswith("/") else f"/{path}"
    url = f"{scheme}://{ip}:{port}{normalized_path}"

    context = None
    if use_https:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

    start = time.perf_counter()
    req = urllib.request.Request(url=url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout_seconds, context=context) as resp:
        status_code = getattr(resp, "status", None)
        if status_code is None:
            status_code = 200
    end = time.perf_counter()

    return int(round((end - start) * 1000)), int(status_code)


def check_server(
    *,
    ip: str,
    port: int,
    do_http_check: bool,
    use_https: bool,
    path: str,
    timeout_seconds: float,
) -> CheckOutcome:
    try:
        tcp_latency_ms = tcp_check(ip, port, timeout_seconds)
    except OSError as exc:
        return CheckOutcome(
            tcp_ok=False,
            tcp_latency_ms=None,
            http_ok=None,
            http_latency_ms=None,
            http_status_code=None,
            error=str(exc),
        )

    if not do_http_check:
        return CheckOutcome(
            tcp_ok=True,
            tcp_latency_ms=tcp_latency_ms,
            http_ok=None,
            http_latency_ms=None,
            http_status_code=None,
            error="",
        )

    try:
        http_latency_ms, status_code = http_check(
            ip=ip,
            port=port,
            use_https=use_https,
            path=path,
            timeout_seconds=timeout_seconds,
        )
        return CheckOutcome(
            tcp_ok=True,
            tcp_latency_ms=tcp_latency_ms,
            http_ok=True,
            http_latency_ms=http_latency_ms,
            http_status_code=status_code,
            error="",
        )
    except urllib.error.HTTPError as exc:
        return CheckOutcome(
            tcp_ok=True,
            tcp_latency_ms=tcp_latency_ms,
            http_ok=False,
            http_latency_ms=None,
            http_status_code=int(getattr(exc, "code", 0) or 0) or None,
            error=str(exc),
        )
    except (urllib.error.URLError, ssl.SSLError, OSError) as exc:
        return CheckOutcome(
            tcp_ok=True,
            tcp_latency_ms=tcp_latency_ms,
            http_ok=False,
            http_latency_ms=None,
            http_status_code=None,
            error=str(exc),
        )
