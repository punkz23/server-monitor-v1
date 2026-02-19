#!/usr/bin/env python
"""Find any valid SSL certificates on servers"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

import paramiko

def find_any_certs():
    print('=== Find Any SSL Certificates ===')
    
    servers = {
        '192.168.254.13': {'username': 'w4-assistant', 'password': 'O6G1Amvos0icqGRC'},
        '192.168.254.50': {'username': 'ws3-assistant', 'password': '6c$7TpzjzYpTpbDp'},
        '192.168.253.15': {'username': 'w1-assistant', 'password': 'hIkLM#X5x1sjwIrM'}
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
            
            # Try different approaches to find certificates
            commands = [
                # Find any .pem files
                "find /etc -name '*.pem' -type f 2>/dev/null | head -5",
                # Check Apache SSL config
                "find /etc/apache2 -name '*.conf' -exec grep -l 'SSLCertificateFile' {} \\; 2>/dev/null | head -3",
                # Check if Apache is listening on 443
                "sudo netstat -tlnp | grep :443",
                # Check Apache config for SSL
                "sudo apache2ctl -S | grep ssl",
                # Try to access SSL directly
                "echo | openssl s_client -connect localhost:443 -servername localhost 2>/dev/null | openssl x509 -noout -subject -dates"
            ]
            
            for cmd in commands:
                print(f'🔧 Command: {cmd}')
                stdin, stdout, stderr = ssh.exec_command(cmd)
                output = stdout.read().decode().strip()
                error = stderr.read().decode().strip()
                
                if output:
                    print(f'✅ Output:\n{output}')
                if error:
                    print(f'❌ Error: {error}')
                print('---')
            
            ssh.close()
            
        except Exception as e:
            print(f'❌ SSH connection failed: {e}')

if __name__ == '__main__':
    find_any_certs()
