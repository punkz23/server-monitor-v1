import paramiko

hostname = "192.168.253.15"
username = "w1-assistant"
password = "hIkLM#X5x1sjwIrM"

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, password=password, timeout=10)
    print(f"Connected to {hostname}")
    
    # Check launcher content
    stdin, stdout, stderr = ssh.exec_command("cat ~/serverwatch-agent/run-agent.sh")
    print(f"Launcher content:\n{stdout.read().decode()}")
    
    # Check if config exists
    stdin, stdout, stderr = ssh.exec_command("ls ~/serverwatch-agent/config.json")
    print(f"Config exists: {stdout.channel.recv_exit_status() == 0}")
    
    # Try running the launcher directly
    print("Executing launcher...")
    stdin, stdout, stderr = ssh.exec_command("cd ~/serverwatch-agent && ./run-agent.sh")
    print(f"Stdout: {stdout.read().decode()}")
    print(f"Stderr: {stderr.read().decode()}")
    
    ssh.close()
except Exception as e:
    print(f"Failed: {e}")
