import paramiko

hostname = "192.168.254.17" # MNL Slave #2
username = "db3-assistant"
password = "c%WCloNUVkjX"

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, password=password, timeout=10)
    print(f"Connected to {hostname}")
    
    # Try to curl the backend
    stdin, stdout, stderr = ssh.exec_command("curl -I http://192.168.253.31:8001/api/info/")
    print(f"Curl result: {stdout.read().decode()}")
    print(f"Curl error: {stderr.read().decode()}")
    
    ssh.close()
except Exception as e:
    print(f"Failed: {e}")
