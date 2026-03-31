import paramiko
hostname = "192.168.254.50"
username = "ws3-assistant"
password = "6c$7TpzjzYpTpbDp" 

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, password=password, timeout=10)
    
    # Try running python command directly from /opt/serverwatch-agent
    print("Running python command directly...")
    cmd = "echo '6c$7TpzjzYpTpbDp' | sudo -S /opt/serverwatch-agent/venv/bin/python /opt/serverwatch-agent/serverwatch-agent.py --config /etc/serverwatch-agent/config.json"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(f"Direct Stdout:\n{stdout.read().decode()}")
    print(f"Direct Stderr:\n{stderr.read().decode()}")
    
    ssh.close()
except Exception as e:
    print(f"Failed: {e}")
