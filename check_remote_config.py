import paramiko

hostname = "192.168.253.15"
username = "w1-assistant"
password = "hIkLM#X5x1sjwIrM"

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, password=password, timeout=10)
    print(f"Connected to {hostname}")
    
    stdin, stdout, stderr = ssh.exec_command("cat ~/serverwatch-agent/config.json")
    print(f"Config content:\n{stdout.read().decode()}")
    
    ssh.close()
except Exception as e:
    print(f"Failed: {e}")
