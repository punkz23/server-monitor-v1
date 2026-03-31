import paramiko
hostname = '192.168.254.5'
username = 's1-assistant'
password = 'K%HyWy3qjXLbUet0' # From previous decrypt

print(f"--- Retrying {hostname} ---")
try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, password=password, timeout=60) # Increased timeout
    
    cmd = "curl -sS https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3 get-pip.py --user --break-system-packages && python3 -m pip install --user --break-system-packages psutil requests"
    ssh.exec_command(cmd)
    print(f"✅ Dependencies installed on {hostname}")
    ssh.close()
except Exception as e:
    print(f"❌ Error: {e}")
