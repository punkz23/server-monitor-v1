from monitor.models import CheckResult, Server

s = Server.objects.get(ip_address='192.168.254.5')
checks = CheckResult.objects.filter(server=s).order_by('-checked_at')[:5]

print('Recent checks for MNL Main DB (192.168.254.5):')
for c in checks:
    print(f'  {c.checked_at.strftime("%H:%M")}: {c.status} (HTTP: {c.http_status_code}, Error: {c.error or "None"}')
