#!/usr/bin/env python
"""Test disk metrics and server status"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.services.metrics_monitor_service import MetricsMonitorService
from monitor.models_ssh_credentials import SSHCredential
from monitor.models import Server

def test_disk_metrics():
    """Test disk metrics for server 192.168.254.13"""
    print('🔍 Testing Disk Metrics for 192.168.254.13')
    print('=' * 50)
    
    server = Server.objects.filter(ip_address='192.168.254.13').first()
    credential = SSHCredential.objects.filter(server=server, is_active=True).first()

    if server and credential:
        print(f'✅ Found server: {server.name}')
        print(f'✅ SSH credentials: {credential.username}@{server.ip_address}:{credential.port}')
        
        monitor = MetricsMonitorService()
        monitor.ssh_credentials[server.ip_address] = {
            'username': credential.username,
            'password': credential.get_password(),
            'port': credential.port
        }
        
        # Test comprehensive metrics
        print('\n📊 Testing Comprehensive Metrics:')
        metrics = monitor.get_comprehensive_metrics(server.ip_address)
        
        if 'current' in metrics:
            current = metrics['current']
            print(f'   CPU: {current.get("cpu", "N/A")}')
            print(f'   RAM: {current.get("ram", "N/A")}')
            print(f'   Disk: {current.get("disk", "N/A")}')
            print(f'   SSL: {current.get("ssl", "N/A")}')
        else:
            print(f'   ❌ Error: {metrics.get("error", "Unknown error")}')
            
        # Test individual disk command
        print('\n💿 Testing Individual Disk Command:')
        try:
            import paramiko
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
            
            # Test the exact command used in metrics service
            stdin, stdout, stderr = ssh.exec_command("df -h / | grep '^/dev/' | awk '{print $5}' | head -1")
            disk_output = stdout.read().decode().strip()
            disk_error = stderr.read().decode().strip()
            
            print(f'   Command: df -h / | grep \'^/dev/\' | awk \'{{print $5}}\' | head -1')
            print(f'   Output: "{disk_output}"')
            print(f'   Error: "{disk_error}"')
            
            if disk_output:
                try:
                    disk_percent = float(disk_output.split()[4].replace('%', ''))
                    print(f'   Parsed: {disk_percent}%')
                except (ValueError, IndexError) as e:
                    print(f'   ❌ Parse error: {e}')
                    
                    # Try fallback parsing
                    for part in disk_output.split():
                        if '%' in part and part.replace('%', '').replace('.', '').isdigit():
                            disk_percent = float(part.replace('%', ''))
                            print(f'   Fallback parsed: {disk_percent}%')
                            break
                    else:
                        print(f'   ❌ Could not parse percentage from: "{disk_output}"')
            else:
                print('   ❌ No output from command')
                
            ssh.close()
            
        except Exception as e:
            print(f'   ❌ SSH error: {e}')
    else:
        print('❌ Server or credentials not found')

def test_server_status():
    """Test server status for 192.168.253.15 and 192.168.253.7"""
    print('\n🔍 Testing Server Status')
    print('=' * 50)
    
    servers_to_test = ['192.168.253.15', '192.168.253.7']
    
    for ip in servers_to_test:
        print(f'\n🖥️ Testing {ip}:')
        server = Server.objects.filter(ip_address=ip).first()
        if server:
            print(f'   Name: {server.name}')
            print(f'   Current Status: {server.get_last_status_display()} ({server.last_status})')
            print(f'   Last Checked: {server.last_checked}')
            print(f'   Last Error: {server.last_error}')
            
            # Test connectivity
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((ip, 80))
                sock.close()
                
                if result == 0:
                    print(f'   Port 80: OPEN')
                else:
                    print(f'   Port 80: CLOSED (result: {result})')
                    
            except Exception as e:
                print(f'   Port test error: {e}')
        else:
            print(f'   ❌ Server not found in database')

if __name__ == '__main__':
    test_disk_metrics()
    test_server_status()
