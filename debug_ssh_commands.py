#!/usr/bin/env python
"""Debug individual SSH commands for server 192.168.254.13"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

import paramiko
from monitor.models_ssh_credentials import SSHCredential
from monitor.models import Server

def test_ssh_commands():
    """Test individual SSH commands"""
    print('🔍 Testing SSH Commands for 192.168.254.13')
    print('=' * 50)
    
    # Get server and credentials
    server = Server.objects.filter(ip_address='192.168.254.13').first()
    if not server:
        print('❌ Server not found')
        return
    
    credential = SSHCredential.objects.filter(server=server, is_active=True).first()
    if not credential:
        print('❌ No credentials found')
        return
    
    print(f'✅ Connecting to {server.ip_address} as {credential.username}')
    
    try:
        # Connect via SSH
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=server.ip_address,
            username=credential.username,
            password=credential.get_password(),
            port=credential.port,
            timeout=10,
            allow_agent=False,
            look_for_keys=False
        )
        
        print('✅ SSH connection established')
        
        # Test CPU command
        print('\n🖥️ Testing CPU Command:')
        try:
            stdin, stdout, stderr = ssh.exec_command("top -bn1 | grep 'Cpu(s)' | sed 's/.*, *\\([0-9.]*\\)% id.*/\\1/' | head -1")
            cpu_output = stdout.read().decode().strip()
            cpu_error = stderr.read().decode().strip()
            
            print(f'   Command: top -bn1 | grep "Cpu(s)" | sed ...')
            print(f'   Output: "{cpu_output}"')
            print(f'   Error: "{cpu_error}"')
            
            if cpu_output and cpu_output.isdigit():
                print(f'   ✅ CPU Usage: {cpu_output}%')
            else:
                print('   ❌ Could not parse CPU usage')
                
        except Exception as e:
            print(f'   ❌ CPU command error: {e}')
        
        # Test alternative CPU command
        print('\n🖥️ Testing Alternative CPU Command:')
        try:
            stdin, stdout, stderr = ssh.exec_command("grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$4+$5)} END {print usage}'")
            cpu_alt = stdout.read().decode().strip()
            cpu_alt_error = stderr.read().decode().strip()
            
            print(f'   Command: grep cpu /proc/stat | awk ...')
            print(f'   Output: "{cpu_alt}"')
            print(f'   Error: "{cpu_alt_error}"')
            
            if cpu_alt:
                try:
                    cpu_percent = float(cpu_alt)
                    print(f'   ✅ Alternative CPU Usage: {cpu_percent:.2f}%')
                except:
                    print('   ❌ Could not parse alternative CPU')
            else:
                print('   ❌ Alternative CPU command failed')
                
        except Exception as e:
            print(f'   ❌ Alternative CPU command error: {e}')
        
        # Test SSL certificate
        print('\n🔒 Testing SSL Certificate:')
        cert_path = '/etc/letsencrypt/live/dailyoverland.com/cert.pem'
        
        # Check if certificate file exists
        try:
            stdin, stdout, stderr = ssh.exec_command(f"test -f {cert_path} && echo 'EXISTS' || echo 'NOT_FOUND'")
            cert_exists = stdout.read().decode().strip()
            print(f'   Certificate Path: {cert_path}')
            print(f'   File Status: {cert_exists}')
            
            if cert_exists == 'EXISTS':
                # Get certificate info
                stdin, stdout, stderr = ssh.exec_command(f"openssl x509 -in {cert_path} -noout -dates")
                cert_output = stdout.read().decode().strip()
                cert_error = stderr.read().decode().strip()
                
                print(f'   Certificate Output: "{cert_output}"')
                print(f'   Certificate Error: "{cert_error}"')
                
                if 'notAfter=' in cert_output:
                    print('   ✅ Certificate readable')
                else:
                    print('   ❌ Could not read certificate')
            else:
                print('   ❌ Certificate file not found')
                
        except Exception as e:
            print(f'   ❌ SSL certificate error: {e}')
        
        # Test system info
        print('\n📋 Testing System Info:')
        try:
            stdin, stdout, stderr = ssh.exec_command("uname -a")
            system_info = stdout.read().decode().strip()
            print(f'   System: {system_info}')
        except Exception as e:
            print(f'   ❌ System info error: {e}')
        
        # Test user permissions
        print('\n👤 Testing User Permissions:')
        try:
            stdin, stdout, stderr = ssh.exec_command("whoami && id")
            user_info = stdout.read().decode().strip()
            print(f'   User Info: {user_info}')
        except Exception as e:
            print(f'   ❌ User info error: {e}')
        
        ssh.close()
        print('\n✅ SSH connection closed')
        
    except Exception as e:
        print(f'❌ SSH connection error: {e}')

def test_alternative_ssl_paths():
    """Test alternative SSL certificate paths"""
    print('\n🔍 Testing Alternative SSL Paths')
    print('=' * 50)
    
    alternative_paths = [
        '/etc/letsencrypt/live/dailyoverland.com/fullchain.pem',
        '/etc/letsencrypt/live/dailyoverland.com/cert.pem',
        '/etc/ssl/certs/dailyoverland.com.crt',
        '/etc/nginx/ssl/dailyoverland.com.crt',
        '/etc/apache2/ssl/dailyoverland.com.crt',
        '/home/w4-assistant/.ssl/dailyoverland.com.crt'
    ]
    
    server = Server.objects.filter(ip_address='192.168.254.13').first()
    credential = SSHCredential.objects.filter(server=server, is_active=True).first()
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=server.ip_address,
            username=credential.username,
            password=credential.get_password(),
            port=credential.port,
            timeout=10,
            allow_agent=False,
            look_for_keys=False
        )
        
        for cert_path in alternative_paths:
            try:
                stdin, stdout, stderr = ssh.exec_command(f"test -f {cert_path} && echo 'EXISTS' || echo 'NOT_FOUND'")
                result = stdout.read().decode().strip()
                status = '✅' if result == 'EXISTS' else '❌'
                print(f'   {status} {cert_path}: {result}')
            except Exception as e:
                print(f'   ❌ {cert_path}: Error - {e}')
        
        ssh.close()
        
    except Exception as e:
        print(f'❌ SSH connection error: {e}')

if __name__ == '__main__':
    test_ssh_commands()
    test_alternative_ssl_paths()
    
    print('\n🎯 Recommendations:')
    print('1. If CPU commands fail, try alternative commands')
    print('2. If SSL certificate not found, update the path in metrics service')
    print('3. Check user permissions for reading certificate files')
    print('4. Verify certificate file locations on server')
