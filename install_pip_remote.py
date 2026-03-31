import paramiko
import json
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.models import Server

# Target web server IPs (excluding .50 which already has pip)
web_ips = [
    '192.168.253.31', '192.168.253.15', '192.168.253.7', 
    '192.168.254.19', '192.168.254.13', '192.168.254.12', 
    '192.168.254.10', '192.168.254.7'
]

for ip in web_ips:
    try:
        s = Server.objects.get(ip_address=ip)
        if not hasattr(s, 'ssh_credential'):
            print(f"Skipping {s.name} ({ip}): No credentials")
            continue
            
        cred = s.ssh_credential
        hostname = s.ip_address
        username = cred.username
        password = cred.get_password()
        
        print(f"\n--- Installing pip on {s.name} ({ip}) ---")
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, username=username, password=password, timeout=15)
        
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
            print(f"✅ Success! Pip installed on {hostname}")
        else:
            print(f"❌ Failed to install pip on {hostname}")
            
        ssh.close()
    except Exception as e:
        print(f"❌ Error on {ip}: {e}")

