import paramiko

hostname = "192.168.253.15"
username = "w1-assistant"
password = "hIkLM#X5x1sjwIrM"

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, password=password, timeout=10)
    print(f"Connected to {hostname}")
    
    # Check pip
    stdin, stdout, stderr = ssh.exec_command("which pip; which pip3; python3 -m pip --version")
    print(f"Pip check:\n{stdout.read().decode()}")
    print(f"Pip error:\n{stderr.read().decode()}")
    
    ssh.close()
except Exception as e:
    print(f"Failed: {e}")
