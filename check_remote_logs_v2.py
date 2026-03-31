import paramiko

hostname = "192.168.253.15"
username = "w1-assistant"
password = "hIkLM#X5x1sjwIrM"

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, password=password, timeout=10)
    print(f"Connected to {hostname}")
    
    # Check if process is running
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep serverwatch-agent | grep -v grep")
    print(f"Process check:\n{stdout.read().decode()}")
    
    # Check logs
    stdin, stdout, stderr = ssh.exec_command("cat ~/serverwatch-agent/agent.log")
    print(f"Logs:\n{stdout.read().decode()}")
    
    ssh.close()
except Exception as e:
    print(f"Failed: {e}")
