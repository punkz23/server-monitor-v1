import paramiko
import json
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.models import Server
from monitor.models_ssh_credentials import SSHCredential
from projects_management.models import Server as PMServer

# Target web server IPs (excluding .50 which already has pip)
web_ips = [
    '192.168.253.31', '192.168.253.15', '192.168.253.7', 
    '192.168.254.19', '192.168.254.13', '192.168.254.12', 
    '192.168.254.10', '192.168.254.7'
]

def get_creds(ip):
    # Try Monitor SSH credentials first
    try:
        s = Server.objects.get(ip_address=ip)
        cred = s.ssh_credential
        return cred.username, cred.get_password()
    except Exception:
        pass
        
    # Try Projects Management credentials
    try:
        pms = PMServer.objects.filter(hostname=ip).first()
        if pms:
            return pms.user, pms.password # PMServer password field is encrypted and auto-decrypted by field
    except Exception:
        pass
        
    return None, None

for ip in web_ips:
    username, password = get_creds(ip)
    if not username:
        print(f"Skipping {ip}: No credentials found in any model")
        continue
        
    print(f"\n--- Installing pip on {ip} (User: {username}) ---")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=username, password=password, timeout=15)
        
        # Download and run get-pip.py
        cmd = "curl -sS https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3 get-pip.py --user"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        
        print(f"STDOUT: {stdout.read().decode().strip()}")
        err = stderr.read().decode().strip()
        if err:
            print(f"STDERR: {err}")
            
        # Verify
        stdin, stdout, stderr = ssh.exec_command("python3 -m pip --version")
        if stdout.channel.recv_exit_status() == 0:
            print(f"✅ Success! Pip installed on {ip}")
        else:
            print(f"❌ Failed to install pip on {ip}")
            
        ssh.close()
    except Exception as e:
        print(f"❌ Error on {ip}: {e}")

