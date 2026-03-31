import paramiko
import json
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.models import Server
from monitor.models_ssh_credentials import SSHCredential

# The failing MNL servers
mnl_subset_ips = ['192.168.254.19', '192.168.254.12', '192.168.254.10']

for ip in mnl_subset_ips:
    try:
        s = Server.objects.get(ip_address=ip)
        cred = s.ssh_credential
        username = cred.username
        password = cred.get_password()
        
        print(f"\n--- Installing pip on {ip} (User: {username}) ---")
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=username, password=password, timeout=60)
        
        # Download and run get-pip.py
        cmd = "curl -sS https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3 get-pip.py --user --break-system-packages"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        
        print(f"STDOUT: {stdout.read().decode().strip()}")
        err = stderr.read().decode().strip()
        if err:
            print(f"STDERR: {err}")
            
        # Manually install deps immediately to be sure
        cmd_install = "python3 -m pip install --user --break-system-packages psutil requests"
        stdin, stdout, stderr = ssh.exec_command(cmd_install)
        print(f"Install Result: {stdout.read().decode().strip()}")
        
        # Restart agent
        ssh.exec_command("cd ~/serverwatch-agent && ./run-agent.sh")
        print("Agent restarted")
            
        ssh.close()
    except Exception as e:
        print(f"❌ Error on {ip}: {e}")

