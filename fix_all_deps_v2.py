import paramiko
import json
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.models import Server
from projects_management.models import Server as PMServer

# Target web server IPs
web_ips = [
    '192.168.253.31', '192.168.253.15', '192.168.253.7', 
    '192.168.254.19', '192.168.254.13', '192.168.254.12', 
    '192.168.254.10', '192.168.254.7'
]

def get_creds(ip):
    try:
        s = Server.objects.get(ip_address=ip)
        if hasattr(s, 'ssh_credential'):
            return s.ssh_credential.username, s.ssh_credential.get_password()
    except Exception:
        pass
    try:
        pms = PMServer.objects.filter(hostname=ip).first()
        if pms:
            return pms.user, pms.password
    except Exception:
        pass
    return None, None

print(f"Starting fix for {len(web_ips)} IPs...")

for ip in web_ips:
    username, password = get_creds(ip)
    if not username:
        print(f"Skipping {ip}: No credentials found")
        continue
        
    print(f"--- Fixing {ip} (User: {username}) ---")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=username, password=password, timeout=20)
        
        # Install psutil/requests
        cmd = "python3 -m pip install --user --break-system-packages psutil requests"
        ssh.exec_command(cmd)
        
        # Wait a bit for install to start, then start agent
        import time
        time.sleep(2)
        ssh.exec_command("cd ~/serverwatch-agent && ./run-agent.sh")
        print(f"✅ Commands sent to {ip}")
        ssh.close()
    except Exception as e:
        print(f"❌ Error on {ip}: {e}")

