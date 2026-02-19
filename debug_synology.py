#!/usr/bin/env python
"""Debug Synology monitoring issue"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.services.server_status_monitor import ServerStatusMonitor
from monitor.models import Server
import requests
import socket
import subprocess

def debug_synology_monitoring():
    print('🔍 Debugging Synology DS918+ (HO) Monitoring Issue')
    print('=' * 60)
    
    ip = '192.168.253.40'
    monitor = ServerStatusMonitor()
    
    # Get server details
    try:
        server = Server.objects.get(ip_address=ip)
        print(f'📋 Server: {server.name} ({server.ip_address})')
        print(f'📊 Current Status: {server.last_status}')
        print(f'⏰ Last Checked: {server.last_checked}')
        print('')
    except Server.DoesNotExist:
        print('❌ Server not found in database')
        return
    
    # Test each monitoring method step by step
    print('🔍 Testing Monitoring Methods:')
    print('')
    
    # Method 1: HTTP request
    print('1️⃣ HTTP Request Test:')
    try:
        response = requests.get(f'http://{ip}', timeout=5)
        print(f'   ✅ SUCCESS: HTTP {response.status_code}')
        print('   ⚠️  This would mark server as UP!')
    except requests.exceptions.RequestException as e:
        print(f'   ❌ FAILED: {e}')
    
    # Method 2: HTTPS request
    print('2️⃣ HTTPS Request Test:')
    try:
        response = requests.get(f'https://{ip}', timeout=5, verify=False)
        print(f'   ✅ SUCCESS: HTTPS {response.status_code}')
        print('   ⚠️  This would mark server as UP!')
    except requests.exceptions.RequestException as e:
        print(f'   ❌ FAILED: {e}')
    
    # Method 3: Port 80 check
    print('3️⃣ Port 80 Check:')
    try:
        sock = socket.create_connection((ip, 80), timeout=5)
        sock.close()
        print('   ✅ SUCCESS: Port 80 open')
        print('   ⚠️  This would mark server as UP!')
    except Exception as e:
        print(f'   ❌ FAILED: {e}')
    
    # Method 4: Port 443 check
    print('4️⃣ Port 443 Check:')
    try:
        sock = socket.create_connection((ip, 443), timeout=5)
        sock.close()
        print('   ✅ SUCCESS: Port 443 open')
        print('   ⚠️  This would mark server as UP!')
    except Exception as e:
        print(f'   ❌ FAILED: {e}')
    
    # Method 5: Ping (the problematic one)
    print('5️⃣ Ping Test:')
    try:
        if os.name == 'nt':  # Windows
            result = subprocess.run(['ping', '-n', '1', ip], 
                                  capture_output=True, text=True, timeout=5)
        else:  # Linux/Mac
            result = subprocess.run(['ping', '-c', '1', ip], 
                                  capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            print('   ✅ SUCCESS: Ping responded')
            print('   ⚠️  This would mark server as UP!')
            print('   🔍 This is likely the issue - ping succeeds but device is off')
        else:
            print('   ❌ FAILED: Ping failed')
    except Exception as e:
        print(f'   ❌ FAILED: {e}')
    
    print('')
    print('🎯 Overall Result:')
    is_up = monitor.check_server_status(ip)
    print(f'📊 Final Status: {"UP" if is_up else "DOWN"}')
    
    print('')
    print('💡 Analysis:')
    if is_up:
        print('❌ ISSUE CONFIRMED: Server shows as UP but should be DOWN')
        print('🔧 The ping method is likely returning false positive')
        print('🛠️  Need to improve monitoring logic for NAS devices')
    else:
        print('✅ Server correctly detected as DOWN')

if __name__ == '__main__':
    debug_synology_monitoring()
