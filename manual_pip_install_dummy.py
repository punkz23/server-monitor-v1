import paramiko

hostname = "192.168.253.31"
username = "ic1"
password = "server"

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, password=password, timeout=15)
    print(f"Connected to {hostname}")
    
    # Try install
    cmd = "python3 -m pip install --user --break-system-packages psutil requests"
    print(f"Running: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(f"STDOUT:\n{stdout.read().decode()}")
    print(f"STDERR:\n{stderr.read().decode()}")
    
    # Verify again
    stdin, stdout, stderr = ssh.exec_command("python3 -c 'import psutil; print(psutil.__version__)'")
    print(f"Import check:\n{stdout.read().decode()}")
    print(f"Import error:\n{stderr.read().decode()}")
    
    ssh.close()
except Exception as e:
    print(f"Failed: {e}")
