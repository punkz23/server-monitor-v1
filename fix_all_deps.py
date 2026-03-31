import paramiko
import json
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.models import Server

# Target web server IPs
web_ips = [
    '192.168.253.31', '192.168.253.15', '192.168.253.7', 
    '192.168.254.19', '192.168.254.13', '192.168.254.12', 
    '192.168.254.10', '192.168.254.7'
]

def get_creds(ip):
    try:
        s = Server.objects.get(ip_address=ip)
        cred = s.ssh_credential
        return cred.username, cred.get_password()
    except Exception:
        return None, None

for ip in web_ips:
    username, password = get_creds(ip)
    if not username: continue
        
    print(f"\n--- Fixing dependencies on {ip} ---")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=username, password=password, timeout=30)
        
        cmd = "python3 -m pip install --user --break-system-packages psutil requests"
        ssh.exec_command(cmd)
        
        # Start the agent using the launcher
        ssh.exec_command("cd ~/serverwatch-agent && ./run-agent.sh")
        print(f"✅ Commands sent to {ip}")
        ssh.close()
    except Exception as e:
        print(f"❌ Error on {ip}: {e}")

