#!/usr/bin/env python
"""Test certificate file access with detailed error reporting"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

import paramiko

def test_certificate_access():
    print('=== Detailed Certificate Access Test ===')
    
    servers = {
        '192.168.254.13': {
            'username': 'w4-assistant',
            'password': 'O6G1Amvos0icqGRC',
            'cert_paths': [
                '/etc/letsencrypt/live/dailyoverland.com/cert.pem',
                '/etc/letsencrypt/archive/dailyoverland.com/cert23.pem'
            ]
        },
        '192.168.254.50': {
            'username': 'ws3-assistant',
            'password': '6c$7TpzjzYpTpbDp',
            'cert_paths': [
                '/etc/letsencrypt/live/id.dailyoverland.com/cert.pem',
                '/etc/letsencrypt/archive/id.dailyoverland.com/cert14.pem'
            ]
        },
        '192.168.253.15': {
            'username': 'w1-assistant',
            'password': 'hIkLM#X5x1sjwIrM',
            'cert_paths': [
                '/etc/letsencrypt/live/ho.employee.dailyoverland.com/cert.pem',
                '/etc/letsencrypt/archive/ho.employee.dailyoverland.com/cert4.pem'
            ]
        }
    }
    
    for ip, server_info in servers.items():
        print(f'\n🔍 Testing {ip} ({server_info["username"]}):')
        
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect
            ssh.connect(
                hostname=ip,
                username=server_info['username'],
                password=server_info['password'],
                timeout=10,
                allow_agent=False,
                look_for_keys=False
            )
            
            for cert_path in server_info['cert_paths']:
                print(f'  📄 Testing: {cert_path}')
                
                # Check file existence and permissions
                commands = [
                    f"test -f {cert_path} && echo 'EXISTS' || echo 'NOT_FOUND'",
                    f"ls -la {cert_path} 2>/dev/null || echo 'NO_ACCESS'",
                    f"file {cert_path} 2>/dev/null || echo 'NO_ACCESS'",
                    f"openssl x509 -in {cert_path} -noout -subject 2>/dev/null || echo 'NO_READ_ACCESS'"
                ]
                
                for cmd in commands:
                    try:
                        stdin, stdout, stderr = ssh.exec_command(cmd)
                        output = stdout.read().decode().strip()
                        error = stderr.read().decode().strip()
                        
                        if output:
                            print(f'    ✅ {cmd.split()[0]}: {output}')
                        if error and "NO_ACCESS" not in error and "NOT_FOUND" not in error:
                            print(f'    ❌ Error: {error}')
                            
                    except Exception as e:
                        print(f'    ❌ Command failed: {e}')
                
                print('')
            
            ssh.close()
            
        except Exception as e:
            print(f'❌ SSH connection failed: {e}')

if __name__ == '__main__':
    test_certificate_access()
