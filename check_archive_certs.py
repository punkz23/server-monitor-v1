#!/usr/bin/env python
"""Check actual certificate files in archive"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

import paramiko

def check_archive_certs():
    print('=== Check Archive Certificate Files ===')
    
    servers = {
        '192.168.254.13': {
            'username': 'w4-assistant',
            'password': 'O6G1Amvos0icqGRC',
            'archive_path': '/etc/letsencrypt/archive/dailyoverland.com/'
        },
        '192.168.254.50': {
            'username': 'ws3-assistant',
            'password': '6c$7TpzjzYpTpbDp',
            'archive_path': '/etc/letsencrypt/archive/id.dailyoverland.com/'
        },
        '192.168.253.15': {
            'username': 'w1-assistant',
            'password': 'hIkLM#X5x1sjwIrM',
            'archive_path': '/etc/letsencrypt/archive/ho.employee.dailyoverland.com/'
        }
    }
    
    for ip, creds in servers.items():
        print(f'\n🔍 Testing {ip}:')
        
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect
            ssh.connect(
                hostname=ip,
                username=creds['username'],
                password=creds['password'],
                timeout=10,
                allow_agent=False,
                look_for_keys=False
            )
            
            archive_path = creds['archive_path']
            print(f'📁 Archive path: {archive_path}')
            
            # List archive files
            stdin, stdout, stderr = ssh.exec_command(f"ls -la {archive_path}")
            files = stdout.read().decode().strip()
            print(f'📄 Archive files:\n{files}')
            
            # Find the latest cert file
            stdin, stdout, stderr = ssh.exec_command(f"ls -t {archive_path}cert*.pem | head -1")
            latest_cert = stdout.read().decode().strip()
            print(f'📄 Latest cert: {latest_cert}')
            
            if latest_cert:
                # Try to read with sudo
                commands = [
                    f"sudo file {latest_cert}",
                    f"sudo openssl x509 -in {latest_cert} -noout -subject -issuer -dates"
                ]
                
                for cmd in commands:
                    print(f'🔧 Command: {cmd}')
                    stdin, stdout, stderr = ssh.exec_command(cmd)
                    output = stdout.read().decode().strip()
                    error = stderr.read().decode().strip()
                    
                    if output:
                        print(f'✅ Output: {output}')
                    if error:
                        print(f'❌ Error: {error}')
                    print('')
            
            ssh.close()
            
        except Exception as e:
            print(f'❌ SSH connection failed: {e}')

if __name__ == '__main__':
    check_archive_certs()
