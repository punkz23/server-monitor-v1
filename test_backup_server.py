#!/usr/bin/env python
"""Test connectivity to MNL Online Booking Backup server"""

import subprocess
import socket
import requests
from datetime import datetime

def test_server_connectivity():
    print('🔍 Testing connectivity to 192.168.254.19:')
    
    # Test 1: Ping
    try:
        result = subprocess.run(['ping', '-n', '2', '192.168.254.19'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print('✅ PING: SUCCESS - Server is reachable')
        else:
            print('❌ PING: FAILED - Server not reachable')
    except Exception as e:
        print(f'❌ PING: ERROR - {e}')
    
    # Test 2: Port 80 (HTTP)
    try:
        sock = socket.create_connection(('192.168.254.19', 80), timeout=5)
        sock.close()
        print('✅ Port 80: OPEN - HTTP service running')
    except Exception as e:
        print(f'❌ Port 80: CLOSED/FAILED - {e}')
    
    # Test 3: Port 443 (HTTPS)
    try:
        sock = socket.create_connection(('192.168.254.19', 443), timeout=5)
        sock.close()
        print('✅ Port 443: OPEN - HTTPS service running')
    except Exception as e:
        print(f'❌ Port 443: CLOSED/FAILED - {e}')
    
    # Test 4: HTTP Request
    try:
        response = requests.get('http://192.168.254.19', timeout=5)
        print(f'✅ HTTP: SUCCESS - Status Code: {response.status_code}')
    except Exception as e:
        print(f'❌ HTTP: FAILED - {e}')
    
    # Test 5: HTTPS Request
    try:
        response = requests.get('https://192.168.254.19', timeout=5, verify=False)
        print(f'✅ HTTPS: SUCCESS - Status Code: {response.status_code}')
    except Exception as e:
        print(f'❌ HTTPS: FAILED - {e}')
    
    print(f'⏰ Test completed at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

if __name__ == '__main__':
    test_server_connectivity()
