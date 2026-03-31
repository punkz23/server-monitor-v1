import paramiko
hostname = "192.168.254.50"
username = "ws3-assistant"
password = "6c$7TpzjzYpTpbDp" # From decrypt

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, password=password, timeout=10)
    
    # Check process
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep serverwatch-agent | grep -v grep")
    print(f"Process:\n{stdout.read().decode()}")
    
    # Check log
    # Note: It used sudo/systemd for this one based on output "Agent service started on..."
    stdin, stdout, stderr = ssh.exec_command("echo '6c$7TpzjzYpTpbDp' | sudo -S tail -n 20 /var/log/serverwatch-agent.log")
    print(f"Logs:\n{stdout.read().decode()}")
    print(f"Stderr:\n{stderr.read().decode()}")
    
    ssh.close()
except Exception as e:
    print(f"Error: {e}")
