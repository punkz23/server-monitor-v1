import paramiko

hostname = "192.168.254.50"
username = "ws3-assistant"
password = "6c$7TpzjzYpTpbDp"

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, password=password, timeout=10)
    print(f"Connected to {hostname}")
    
    # Ping test
    print("Pinging backend...")
    stdin, stdout, stderr = ssh.exec_command("ping -c 4 192.168.253.31")
    print(f"Ping result:\n{stdout.read().decode()}")
    
    # Curl test
    print("Curling backend...")
    stdin, stdout, stderr = ssh.exec_command("curl -v http://192.168.253.31:8001/api/info/ --connect-timeout 5")
    print(f"Curl result:\n{stdout.read().decode()}")
    print(f"Curl error:\n{stderr.read().decode()}")
    
    ssh.close()
except Exception as e:
    print(f"Failed: {e}")
