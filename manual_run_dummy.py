import paramiko

hostname = "192.168.253.31"
username = "ic1"
password = "server"

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, password=password, timeout=10)
    print(f"Connected to {hostname}")
    
    # Run agent directly and capture output
    print("Executing run-agent.sh manually...")
    stdin, stdout, stderr = ssh.exec_command("cd ~/serverwatch-agent && ./run-agent.sh")
    print(f"Launcher Stdout:\n{stdout.read().decode()}")
    print(f"Launcher Stderr:\n{stderr.read().decode()}")
    
    # Wait and check process
    import time
    time.sleep(2)
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep serverwatch-agent | grep -v grep")
    print(f"Process check after run:\n{stdout.read().decode()}")
    
    # Try running python command directly to see errors
    print("Running python command directly...")
    stdin, stdout, stderr = ssh.exec_command("cd ~/serverwatch-agent && python3 serverwatch-agent.py --config config.json")
    print(f"Direct Stdout:\n{stdout.read().decode()}")
    print(f"Direct Stderr:\n{stderr.read().decode()}")
    
    ssh.close()
except Exception as e:
    print(f"Failed: {e}")
