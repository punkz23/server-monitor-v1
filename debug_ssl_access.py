#!/usr/bin/env python
"""Debug SSL certificate file access"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

import paramiko

def debug_cert_access():
    print('=== Debug SSL Certificate File Access ===')
    
    servers = {
        '192.168.254.13': {
            'username': 'w4-assistant',
            'password': 'O6G1Amvos0icqGRC',
            'cert_path': '/etc/letsencrypt/live/dailyoverland.com/cert.pem'
        },
        '192.168.254.50': {
            'username': 'ws3-assistant',
            'password': '6c$7TpzjzYpTpbDp',
            'cert_path': '/etc/letsencrypt/live/id.dailyoverland.com/cert.pem'
        },
        '192.168.253.15': {
            'username': 'w1-assistant',
            'password': 'hIkLM#X5x1sjwIrM',
            'cert_path': '/etc/letsencrypt/live/ho.employee.dailyoverland.com/cert.pem'
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
            
            # Check certificate file
            cert_file = creds['cert_path']
            print(f'📄 Checking: {cert_file}')
            
            # Test file existence with different methods
            commands = [
                f"test -f {cert_file} && echo 'FILE_EXISTS' || echo 'FILE_NOT_FOUND'",
                f"ls -la {cert_file}",
                f"file {cert_file}",
                f"openssl x509 -in {cert_file} -noout -subject | head -1"
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
    debug_cert_access()
