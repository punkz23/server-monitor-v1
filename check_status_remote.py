import paramiko

hostname = "192.168.253.15"
username = "w1-assistant"
password = "hIkLM#X5x1sjwIrM"

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, password=password, timeout=10)
    print(f"Connected to {hostname}")
    
    # Check dependencies
    stdin, stdout, stderr = ssh.exec_command("python3 -c 'import psutil; print(f\"psutil ok: {psutil.__version__}\")'")
    print(stdout.read().decode().strip() or stderr.read().decode().strip())
    
    # Check process
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep serverwatch-agent | grep -v grep")
    print(f"Process check:\n{stdout.read().decode()}")
    
    # Check last logs
    stdin, stdout, stderr = ssh.exec_command("tail -n 20 ~/serverwatch-agent/agent.log")
    print(f"Last logs:\n{stdout.read().decode()}")
    
    ssh.close()
except Exception as e:
    print(f"Failed: {e}")
