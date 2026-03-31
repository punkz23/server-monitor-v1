import paramiko

hostname = "192.168.253.9"
username = "ho-db2-assistant"
password = "hJ4S*mm5j%zi"

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, password=password, timeout=10)
    print(f"Connected to {hostname}")
    
    # Check if files exist
    stdin, stdout, stderr = ssh.exec_command("ls -l /tmp/install.sh")
    print(f"Install script: {stdout.read().decode()}")
    
    # Try running install.sh manually
    print("Running install.sh...")
    stdin, stdout, stderr = ssh.exec_command("cd /tmp && bash install.sh --user")
    print(f"Stdout:\n{stdout.read().decode()}")
    print(f"Stderr:\n{stderr.read().decode()}")
    
    ssh.close()
except Exception as e:
    print(f"Failed: {e}")
