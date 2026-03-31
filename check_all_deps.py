import paramiko
import json

with open('agent_config_batch.json', 'r') as f:
    config = json.load(f)

results = []

for server in config['servers']:
    hostname = server['hostname']
    username = server['username']
    password = server['password']
    
    print(f"Checking {hostname}...")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, username=username, password=password, timeout=10)
        
        # Check pip
        stdin, stdout, stderr = ssh.exec_command("python3 -m pip --version")
        has_pip = stdout.channel.recv_exit_status() == 0
        
        # Check venv
        stdin, stdout, stderr = ssh.exec_command("python3 -m venv --help")
        has_venv = stdout.channel.recv_exit_status() == 0
        
        results.append({
            "hostname": hostname,
            "has_pip": has_pip,
            "has_venv": has_venv
        })
        ssh.close()
    except Exception as e:
        results.append({
            "hostname": hostname,
            "error": str(e)
        })

print("\n--- DEPENDENCY AUDIT RESULTS ---")
for r in results:
    if "error" in r:
        print(f"{r['hostname']}: Connection Error ({r['error']})")
    else:
        status = "OK" if r['has_pip'] and r['has_venv'] else "MISSING DEPS"
        pip_status = "Yes" if r['has_pip'] else "No"
        venv_status = "Yes" if r['has_venv'] else "No"
        print(f"{r['hostname']}: pip={pip_status}, venv={venv_status} -> {status}")

with open('dep_audit_results.json', 'w') as f:
    json.dump(results, f, indent=2)
