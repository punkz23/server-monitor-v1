import paramiko
import sys

hostname = "192.168.253.9"
username = "ho-db2-assistant"
password = "hJ4S*mm5j%zi"

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, password=password, timeout=10)
    print(f"Connected to {hostname}")
    
    # Check if agent directory exists
    stdin, stdout, stderr = ssh.exec_command("ls -d ~/serverwatch-agent")
    if stdout.channel.recv_exit_status() == 0:
        print("Agent directory exists")
        # Check if process is running
        stdin, stdout, stderr = ssh.exec_command("ps aux | grep serverwatch-agent | grep -v grep")
        out = stdout.read().decode()
        if out:
            print(f"Agent process found:\n{out}")
        else:
            print("Agent process NOT found")
    else:
        print("Agent directory NOT found")
    
    ssh.close()
except Exception as e:
    print(f"Connection failed: {e}")
