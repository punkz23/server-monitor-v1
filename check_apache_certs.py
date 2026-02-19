#!/usr/bin/env python
"""Check if certificates need Apache restart and verify new certs"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

import paramiko

def check_apache_and_certs():
    print('=== Check Apache Status and New Certificates ===')
    
    servers = {
        '192.168.254.13': {'username': 'w4-assistant', 'password': 'O6G1Amvos0icqGRC'},
        '192.168.254.50': {'username': 'ws3-assistant', 'password': '6c$7TpzjzYpTpbDp'},
        '192.168.253.15': {'username': 'w1-assistant', 'password': 'hIkLM#X5x1sjwIrM'}
    }
    
    for ip, creds in servers.items():
        print(f'\n🔍 Checking {ip}:')
        
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
            
            # Check Apache status
            stdin, stdout, stderr = ssh.exec_command("systemctl status apache2 --no-pager -l")
            apache_status = stdout.read().decode().strip()
            print(f'🌐 Apache Status: {apache_status.split("Active:")[1].split(";")[0].strip() if "Active:" in apache_status else "Unknown"}')
            
            # Check if Apache needs restart (check cert modification time)
            stdin, stdout, stderr = ssh.exec_command("find /etc/letsencrypt -name 'cert*.pem' -exec ls -la {} \\; 2>/dev/null | head -3")
            cert_files = stdout.read().decode().strip()
            print(f'📄 Recent cert files:\n{cert_files}')
            
            # Check current SSL certificate via direct connection
            stdin, stdout, stderr = ssh.exec_command("echo | openssl s_client -connect localhost:443 -servername localhost 2>/dev/null | openssl x509 -noout -subject -dates")
            current_cert = stdout.read().decode().strip()
            print(f'🔒 Current SSL cert:\n{current_cert}')
            
            # Suggest Apache restart if needed
            if "Dec 29 11:04:17 2025 GMT" in current_cert or "Dec 29 00:06:46 2025 GMT" in current_cert or "Nov 26 04:42:38 2025 GMT" in current_cert:
                print('⚠️ Certificate still shows old expiration date')
                print('💡 Consider restarting Apache: sudo systemctl restart apache2')
            else:
                print('✅ Certificate appears to be updated')
            
            ssh.close()
            
        except Exception as e:
            print(f'❌ Error: {e}')

if __name__ == '__main__':
    check_apache_and_certs()
