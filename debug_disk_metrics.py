#!/usr/bin/env python
"""Debug disk metrics collection for server 192.168.254.13"""

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

def test_disk_commands():
    """Test different disk usage commands"""
    print('🔍 Testing Disk Usage Commands for 192.168.254.13')
    print('=' * 50)
    
    # Get server and credentials
    server = Server.objects.filter(ip_address='192.168.254.13').first()
    if not server:
        print('❌ Server not found')
        return
    
    credential = SSHCredential.objects.filter(server=server, is_active=True).first()
    if not credential:
        print('❌ No SSH credentials found')
        return
    
    print(f'✅ Found server: {server.name}')
    print(f'✅ SSH credentials: {credential.username}@{server.ip_address}:{credential.port}')
    
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
        
        # Test current command
        print('\n🖥️ Testing Current Command:')
        try:
            stdin, stdout, stderr = ssh.exec_command("df -h / | tail -1 | awk '{print $5}' | sed 's/%//'")
            disk_output = stdout.read().decode().strip()
            disk_error = stderr.read().decode().strip()
            
            print(f'   Command: df -h / | tail -1 | awk \'{{print $5}}\' | sed \'s/%//\'')
            print(f'   Output: "{disk_output}"')
            print(f'   Error: "{disk_error}"')
            
            if disk_output:
                try:
                    disk_percent = float(disk_output.replace('%', ''))
                    print(f'   Parsed: {disk_percent}%')
                except ValueError:
                    print(f'   ❌ Could not parse percentage from: "{disk_output}"')
            else:
                print('   ❌ No output')
        except Exception as e:
            print(f'   ❌ Exception: {e}')
        
        # Test alternative commands
        print('\n🔧 Testing Alternative Commands:')
        
        # Test df with different format
        try:
            stdin, stdout, stderr = ssh.exec_command("df -h / | grep -E '^/dev/' | awk '{print $5}' | sed 's/%//'")
            disk_output = stdout.read().decode().strip()
            print(f'   df -h / | grep -E \'^/dev/\' | awk \'{{print $5}}\' | sed \'s/%//\'": "{disk_output}"')
        except Exception as e:
            print(f'   ❌ Alternative command failed: {e}')
        
        # Test basic df
        try:
            stdin, stdout, stderr = ssh.exec_command("df -h /")
            disk_output = stdout.read().decode().strip()
            print(f'   df -h /: "{disk_output[:200]}..."')
        except Exception as e:
            print(f'   ❌ Basic df failed: {e}')
        
        # Test lsblk
        try:
            stdin, stdout, stderr = ssh.exec_command("lsblk | grep -E '^disk' | awk '{print $4}' | head -1")
            disk_output = stdout.read().decode().strip()
            print(f'   lsblk: "{disk_output}"')
        except Exception as e:
            print(f'   ❌ lsblk failed: {e}')
        
        ssh.close()
        
    except Exception as e:
        print(f'❌ SSH connection failed: {e}')

if __name__ == '__main__':
    test_disk_commands()
