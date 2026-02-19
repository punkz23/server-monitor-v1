#!/usr/bin/env python
"""Restart Apache to load new SSL certificates"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

import paramiko

def restart_apache():
    print('=== Restart Apache to Load New SSL Certificates ===')
    
    servers = {
        '192.168.254.13': {'username': 'w4-assistant', 'password': 'O6G1Amvos0icqGRC'},
        '192.168.254.50': {'username': 'ws3-assistant', 'password': '6c$7TpzjzYpTpbDp'},
        '192.168.253.15': {'username': 'w1-assistant', 'password': 'hIkLM#X5x1sjwIrM'}
    }
    
    for ip, creds in servers.items():
        print(f'\n🔄 Restarting Apache on {ip}:')
        
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
            
            # Restart Apache using echo for password
            stdin, stdout, stderr = ssh.exec_command(f"echo '{creds['password']}' | sudo -S systemctl restart apache2")
            restart_output = stdout.read().decode().strip()
            restart_error = stderr.read().decode().strip()
            
            if restart_error and "incorrect password" not in restart_error.lower():
                print(f'⚠️ Restart output: {restart_error}')
            
            # Check if restart was successful
            stdin, stdout, stderr = ssh.exec_command("systemctl is-active apache2")
            apache_status = stdout.read().decode().strip()
            
            if apache_status == "active":
                print(f'✅ Apache restarted successfully on {ip}')
                
                # Check new certificate
                stdin, stdout, stderr = ssh.exec_command("echo | openssl s_client -connect localhost:443 -servername localhost 2>/dev/null | openssl x509 -noout -dates")
                new_cert = stdout.read().decode().strip()
                print(f'🔒 New certificate dates:\n{new_cert}')
            else:
                print(f'❌ Apache restart failed on {ip}: {apache_status}')
            
            ssh.close()
            
        except Exception as e:
            print(f'❌ Error restarting Apache on {ip}: {e}')

if __name__ == '__main__':
    restart_apache()
