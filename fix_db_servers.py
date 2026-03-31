import paramiko
import json
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.models import Server
from monitor.models_ssh_credentials import SSHCredential

# The 5 DB servers missing pip + .50 which just needs redeploy
db_ips = [
    '192.168.253.9', '192.168.253.5', '192.168.254.5', 
    '192.168.254.15', '192.168.254.17', '192.168.254.50'
]

def get_creds(ip):
    try:
        s = Server.objects.get(ip_address=ip)
        cred = s.ssh_credential
        return cred.username, cred.get_password()
    except Exception:
        return None, None

for ip in db_ips:
    username, password = get_creds(ip)
    if not username:
        print(f"Skipping {ip}: No credentials")
        continue
        
    print(f"\n--- Fixing dependencies on {ip} (User: {username}) ---")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=username, password=password, timeout=30)
        
        # Install pip/deps (skip for .50 if it has them, but safe to rerun)
        print("Installing pip and dependencies...")
        cmd = "curl -sS https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3 get-pip.py --user --break-system-packages"
        ssh.exec_command(cmd)
        
        # Install libraries
        cmd = "python3 -m pip install --user --break-system-packages psutil requests"
        ssh.exec_command(cmd)
        
        print(f"✅ Dependencies installed on {ip}")
        ssh.close()
    except Exception as e:
        print(f"❌ Error on {ip}: {e}")

