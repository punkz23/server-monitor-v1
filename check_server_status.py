from monitor.models import CheckResult, Server
from django.utils import timezone
from datetime import timedelta

server = Server.objects.get(ip_address='192.168.254.5')
recent_checks = CheckResult.objects.filter(
    server=server
).order_by('-checked_at')[:10]

print(f'Server: {server.name} ({server.ip_address})')
for check in recent_checks:
    status = 'UP' if check.status == 'UP' else 'DOWN'
    print(f'  {check.checked_at.strftime("%Y-%m-%d %H:%M:%S")}: {status} (HTTP: {check.http_status_code or "N/A"}, Latency: {check.latency_ms or "N/A"}ms)')
