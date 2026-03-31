import paramiko
hostname = "192.168.254.50"
username = "ws3-assistant"
password = "6c$7TpzjzYpTpbDp" 

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, password=password, timeout=10)
    
    cmd = "cat /home/ws3-assistant/serverwatch-agent/config.json"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(f"Config content:\n{stdout.read().decode()}")
    
    ssh.close()
except Exception as e:
    print(f"Failed: {e}")
