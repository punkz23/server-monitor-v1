#!/usr/bin/env python
"""Test server connectivity and performance"""

import requests
import socket
import subprocess
import time

def test_server_connectivity():
    ip = '192.168.253.15'
    
    print(f'🔍 Testing HO Web Server (New - Laravel) at {ip}:')
    print('=' * 50)
    
    # Test HTTP request
    start_time = time.time()
    try:
        response = requests.get(f'http://{ip}', timeout=10)
        elapsed = time.time() - start_time
        print(f'✅ HTTP Request: SUCCESS - Status {response.status_code} ({elapsed:.2f}s)')
        print(f'   📄 Content-Type: {response.headers.get("Content-Type", "Unknown")}')
        print(f'   📏 Content-Length: {response.headers.get("Content-Length", "Unknown")}')
    except Exception as e:
        elapsed = time.time() - start_time
        print(f'❌ HTTP Request: FAILED - {e} ({elapsed:.2f}s)')
    
    # Test HTTPS request
    start_time = time.time()
    try:
        response = requests.get(f'https://{ip}', timeout=10, verify=False)
        elapsed = time.time() - start_time
        print(f'✅ HTTPS Request: SUCCESS - Status {response.status_code} ({elapsed:.2f}s)')
    except Exception as e:
        elapsed = time.time() - start_time
        print(f'❌ HTTPS Request: FAILED - {e} ({elapsed:.2f}s)')
    
    # Test port 80
    start_time = time.time()
    try:
        sock = socket.create_connection((ip, 80), timeout=10)
        sock.close()
        elapsed = time.time() - start_time
        print(f'✅ Port 80: SUCCESS - Port open ({elapsed:.2f}s)')
    except Exception as e:
        elapsed = time.time() - start_time
        print(f'❌ Port 80: FAILED - {e} ({elapsed:.2f}s)')
    
    # Test port 443
    start_time = time.time()
    try:
        sock = socket.create_connection((ip, 443), timeout=10)
        sock.close()
        elapsed = time.time() - start_time
        print(f'✅ Port 443: SUCCESS - Port open ({elapsed:.2f}s)')
    except Exception as e:
        elapsed = time.time() - start_time
        print(f'❌ Port 443: FAILED - {e} ({elapsed:.2f}s)')
    
    # Test ping
    start_time = time.time()
    try:
        result = subprocess.run(['ping', '-n', '2', ip], capture_output=True, text=True, timeout=10)
        elapsed = time.time() - start_time
        if result.returncode == 0:
            print(f'✅ Ping: SUCCESS ({elapsed:.2f}s)')
        else:
            print(f'❌ Ping: FAILED ({elapsed:.2f}s)')
    except Exception as e:
        elapsed = time.time() - start_time
        print(f'❌ Ping: ERROR - {e} ({elapsed:.2f}s)')

if __name__ == '__main__':
    test_server_connectivity()
