import paramiko

hostname = "192.168.253.15"
username = "w1-assistant"
password = "hIkLM#X5x1sjwIrM"

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, password=password, timeout=10)
    print(f"Connected to {hostname}")
    
    # Run agent directly and capture output
    print("Running agent directly with python3...")
    stdin, stdout, stderr = ssh.exec_command("cd ~/serverwatch-agent && python3 serverwatch-agent.py --config config.json")
    print(f"Stdout:\n{stdout.read().decode()}")
    print(f"Stderr:\n{stderr.read().decode()}")
    
    ssh.close()
except Exception as e:
    print(f"Failed: {e}")
