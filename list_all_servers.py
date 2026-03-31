import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.models import Server

def list_all_servers():
    servers = Server.objects.all().order_by('name')
    print(f"{'Name':<25} {'IP Address':<15} {'Status':<10} {'Last Checked':<20}")
    print("-" * 75)
    for server in servers:
        last_checked = server.last_checked.strftime('%Y-%m-%d %H:%M:%S') if server.last_checked else "Never"
        print(f"{server.name:<25} {server.ip_address:<15} {server.last_status:<10} {last_checked:<20}")

if __name__ == "__main__":
    list_all_servers()
