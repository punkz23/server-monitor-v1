import paramiko

hostname = "192.168.253.15"
username = "w1-assistant"
password = "hIkLM#X5x1sjwIrM"

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, password=password, timeout=10)
    print(f"Connected to {hostname}")
    
    # Kill and remove
    ssh.exec_command("ps aux | grep serverwatch-agent | grep -v grep | awk '{print $2}' | xargs -r kill -9")
    ssh.exec_command("rm -rf ~/.serverwatch-agent ~/serverwatch-agent")
    print("Cleaned up old agent files and processes")
    
    ssh.close()
except Exception as e:
    print(f"Failed: {e}")
