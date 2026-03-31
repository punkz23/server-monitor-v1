import paramiko

hostname = "192.168.253.31"
username = "ic1"
password = "server"

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, password=password, timeout=10)
    print(f"Connected to {hostname}")
    
    # Check pip list
    stdin, stdout, stderr = ssh.exec_command("python3 -m pip list | grep psutil")
    print(f"Pip list psutil:\n{stdout.read().decode()}")
    
    # Check install log if it was redirected (though it wasn't in the install script)
    # Check where pip installs things
    stdin, stdout, stderr = ssh.exec_command("python3 -m pip show psutil")
    print(f"Pip show psutil:\n{stdout.read().decode()}")
    
    ssh.close()
except Exception as e:
    print(f"Failed: {e}")
