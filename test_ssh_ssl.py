#!/usr/bin/env python
"""Test SSH connection and find SSL certificate paths"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.services.remote_ssl_certificate_monitor import RemoteSSLCertificateMonitor

def test_ssh_connections():
    print('=== Testing SSH Connections and Finding SSL Certificates ===')
    
    remote_monitor = RemoteSSLCertificateMonitor()
    
    for ip, creds in remote_monitor.ssh_credentials.items():
        print(f'\n🔍 Testing {creds["server_name"]} ({ip}):')
        
        try:
            import paramiko
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
            
            print(f'✅ SSH connection successful')
            
            # Check if Let's Encrypt directory exists
            stdin, stdout, stderr = ssh.exec_command(f"test -d {creds['cert_path']} && echo 'exists' || echo 'not_found'")
            cert_dir_exists = stdout.read().decode().strip()
            print(f'📁 Certificate directory {creds["cert_path"]}: {cert_dir_exists}')
            
            if cert_dir_exists == 'exists':
                # List files in directory
                stdin, stdout, stderr = ssh.exec_command(f"ls -la {creds['cert_path']}")
                files = stdout.read().decode().strip()
                print(f'📄 Files in directory:\n{files}')
            else:
                # Try to find Let's Encrypt certificates
                print('🔍 Searching for Let\'Encrypt certificates...')
                stdin, stdout, stderr = ssh.exec_command("find /etc/letsencrypt -name '*.pem' -type f 2>/dev/null | head -10")
                cert_files = stdout.read().decode().strip()
                if cert_files:
                    print(f'📄 Found certificate files:\n{cert_files}')
                else:
                    print('❌ No Let\'Encrypt certificates found')
            
            # Check if nginx/apache is running and what domains it serves
            stdin, stdout, stderr = ssh.exec_command("systemctl status nginx 2>/dev/null | grep 'Active:' || echo 'nginx not running'")
            nginx_status = stdout.read().decode().strip()
            print(f'🌐 Nginx: {nginx_status}')
            
            stdin, stdout, stderr = ssh.exec_command("systemctl status apache2 2>/dev/null | grep 'Active:' || echo 'apache not running'")
            apache_status = stdout.read().decode().strip()
            print(f'🌐 Apache: {apache_status}')
            
            ssh.close()
            
        except Exception as e:
            print(f'❌ SSH connection failed: {e}')

if __name__ == '__main__':
    test_ssh_connections()
