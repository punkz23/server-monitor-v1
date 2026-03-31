import paramiko
import json
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.models import Server
from monitor.models_ssh_credentials import SSHCredential

# Servers that need dependency fixes and redeployment
offline_ips = [
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

for ip in offline_ips:
    username, password = get_creds(ip)
    if not username:
        print(f"Skipping {ip}: No credentials found")
        continue
        
    print(f"\n--- Fixing dependencies on {ip} (User: {username}) ---")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=username, password=password, timeout=30)
        
        # Install pip/deps
        print("Installing pip and dependencies...")
        cmd = "curl -sS https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3 get-pip.py --user --break-system-packages"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(f"STDOUT: {stdout.read().decode().strip()}")
        err = stderr.read().decode().strip()
        if err:
            print(f"STDERR: {err}")
            
        # Install libraries immediately
        cmd_install = "python3 -m pip install --user --break-system-packages psutil requests"
        stdin, stdout, stderr = ssh.exec_command(cmd_install)
        print(f"Dependencies install result: {stdout.read().decode().strip()}")
        if stderr.read().decode().strip():
            print(f"Dependencies install error: {stderr.read().decode().strip()}")
            
        print(f"Dependencies fixed on {ip}")
        ssh.close()
    except Exception as e:
        print(f"❌ Error on {ip}: {e}")

# Now generate config and redeploy for these servers
print("\n--- Generating configuration for redeployment ---")
# Re-using deploy_agents.py logic to create config
# This requires the AgentDeployer class and its methods to be available
# For simplicity, directly creating the JSON here.
# If deploy_agents.py needs to be run, it should be done separately.

# Placeholder: Actual redeployment will be a separate step.
print("Configuration generation logic would go here, then call deploy_agents.py.")

