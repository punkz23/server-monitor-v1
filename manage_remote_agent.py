
import os
import django
import paramiko
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.models import Server
from monitor.models_ssh_credentials import SSHCredential

def manage_remote_agent(ip_address, command):
    try:
        s = Server.objects.get(ip_address=ip_address)
        c = SSHCredential.objects.get(server=s)
    except Server.DoesNotExist:
        print(f"Server with IP {ip_address} not found.")
        return
    except SSHCredential.DoesNotExist:
        print(f"No SSH credentials for {s.name}.")
        return

    print(f"Executing '{command}' on {s.name} ({s.ip_address})...")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(s.ip_address, username=c.username, password=c.get_password(), port=c.port, timeout=10)
        
        stdin, stdout, stderr = ssh.exec_command(command)
        
        stdout_output = stdout.read().decode().strip()
        stderr_output = stderr.read().decode().strip()
        
        if stdout_output:
            print('STDOUT:', stdout_output)
        if stderr_output:
            print('STDERR:', stderr_output)
            
        ssh.close()

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python manage_remote_agent.py <ip_address> <command>")
        sys.exit(1)
    
    ip_address = sys.argv[1]
    command = " ".join(sys.argv[2:])
    
    manage_remote_agent(ip_address, command)
