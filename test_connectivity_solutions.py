#!/usr/bin/env python
"""
Test connectivity and create working solution
"""

import os
import sys
import django

# Set up Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.models import CCTVDevice
from monitor.dahua_http_api import check_dahua_camera_status
from monitor.dahua_rpc import test_dahua_connection
import requests

def test_working_solutions():
    """Test what connectivity methods work"""
    
    print("=" * 60)
    print("CONNECTIVITY SOLUTIONS TEST")
    print("=" * 60)
    
    devices = CCTVDevice.objects.all()
    
    for device in devices:
        print(f"\n{'='*40}")
        print(f"Device: {device.name}")
        print(f"Domain: {device.domain}")
        print(f"Port: {device.port}")
        print(f"{'='*40}")
        
        # Test 1: Check if domain is IP address
        print(f"\n1. Domain type check...")
        try:
            # Try to resolve as IP
            import socket
            socket.inet_aton(device.domain)
            print(f"   {device.domain} is an IP address")
            is_ip = True
        except:
            print(f"   {device.domain} is NOT an IP address (P2P serial)")
            is_ip = False
        
        # Test 2: Try different port combinations
        if is_ip:
            ports_to_try = [80, 37777, 554, 8080, 8000]
        else:
            ports_to_try = [37777, 80, 8080, 8000]
        
        for port in ports_to_try:
            print(f"\n2. Testing {device.domain}:{port}...")
            
            # Test HTTP connection
            try:
                response = requests.get(f'http://{device.domain}:{port}/', timeout=3)
                print(f"   HTTP {response.status_code} - Server reachable")
                
                # If we get here, try Dahua HTTP API
                if port in [80, 37777]:
                    try:
                        result = check_dahua_camera_status(
                            device.domain, port, 
                            device.username, device.password
                        )
                        print(f"   Dahua API: {'SUCCESS' if result else 'FAILED'}")
                    except Exception as e:
                        print(f"   Dahua API Error: {str(e)[:50]}")
                
            except requests.exceptions.Timeout:
                print(f"   HTTP Timeout - Port may be filtered")
            except requests.exceptions.ConnectionError:
                print(f"   HTTP Connection Failed")
            except Exception as e:
                print(f"   HTTP Error: {str(e)[:50]}")
            
            # Test TCP socket connection
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result = sock.connect_ex((device.domain, port))
                sock.close()
                
                if result == 0:
                    print(f"   TCP Socket: SUCCESS - Port open")
                else:
                    print(f"   TCP Socket: FAILED - Port closed")
            except Exception as e:
                print(f"   TCP Socket Error: {str(e)[:50]}")
        
        # Test 3: Try RPC if IP address
        if is_ip:
            print(f"\n3. Testing RPC connection...")
            try:
                rpc_result = test_dahua_connection(
                    device.domain, device.username, device.password
                )
                print(f"   RPC Result: {'SUCCESS' if rpc_result else 'FAILED'}")
            except Exception as e:
                print(f"   RPC Error: {str(e)[:50]}")
        
        # Test 4: Generate working RTSP URL
        print(f"\n4. Generating RTSP URLs...")
        
        # Standard Dahua RTSP formats
        rtsp_formats = [
            f"rtsp://{device.username}:{device.password}@{device.domain}:554/cam/realmonitor?channel=1&subtype=0",
            f"rtsp://{device.username}:{device.password}@{device.domain}:554/cam/realmonitor?channel=1&subtype=1",
            f"rtsp://{device.username}:{device.password}@{device.domain}:554/stream1",
            f"rtsp://{device.username}:{device.password}@{device.domain}:554/live/0",
            f"rtsp://{device.username}:{device.password}@{device.domain}:554/h264/ch1/main/av_stream",
        ]
        
        for i, url in enumerate(rtsp_formats, 1):
            print(f"   Format {i}: {url}")
    
    print(f"\n{'='*60}")
    print("RECOMMENDATIONS:")
    print("1. For IP-based devices: Use HTTP API or RPC")
    print("2. For P2P devices: Need actual IP addresses")
    print("3. Test RTSP URLs with VLC player")
    print("4. Check network firewall settings")
    print(f"{'='*60}")

if __name__ == "__main__":
    test_working_solutions()
