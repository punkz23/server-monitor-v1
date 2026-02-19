#!/usr/bin/env python
"""
Test script to check actual CCTV connectivity
"""

import os
import sys
import django

# Set up Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.models import CCTVDevice
from monitor.dahua_rpc import test_dahua_connection, get_dahua_live_feed
from monitor.dahua_http_api import check_dahua_camera_status
from monitor.dahua_api import check_dahua_device_status

def test_all_devices():
    """Test connectivity to all CCTV devices"""
    
    print("=" * 60)
    print("CCTV CONNECTIVITY TEST")
    print("=" * 60)
    
    devices = CCTVDevice.objects.all()
    
    if not devices:
        print("No CCTV devices found in database.")
        print("Please import devices first using the XML import feature.")
        return
    
    print(f"Found {devices.count()} devices to test...\n")
    
    for device in devices:
        print(f"\n{'='*40}")
        print(f"Testing: {device.name}")
        print(f"Domain: {device.domain}")
        print(f"Port: {device.port}")
        print(f"Username: {device.username}")
        print(f"Password: {'*' * len(device.password)}")
        print(f"{'='*40}")
        
        # Test 1: Basic Dahua API check
        print("\n1. Testing Dahua API connection...")
        try:
            api_result = check_dahua_device_status(device.domain, device.port)
            print(f"   API Result: {'SUCCESS' if api_result else 'FAILED'}")
        except Exception as e:
            print(f"   API Error: {e}")
        
        # Test 2: Dahua RPC connection
        print("\n2. Testing Dahua RPC connection...")
        try:
            rpc_result = test_dahua_connection(
                device.domain, 
                device.username, 
                device.password
            )
            print(f"   RPC Result: {'SUCCESS' if rpc_result else 'FAILED'}")
        except Exception as e:
            print(f"   RPC Error: {e}")
        
        # Test 3: HTTP API check (for IP addresses)
        print("\n3. Testing HTTP API connection...")
        try:
            http_result = check_dahua_camera_status(
                device.domain,
                device.port,
                device.username,
                device.password
            )
            print(f"   HTTP Result: {'SUCCESS' if http_result else 'FAILED'}")
        except Exception as e:
            print(f"   HTTP Error: {e}")
        
        # Test 4: Live feed test
        print("\n4. Testing live feed...")
        try:
            live_feed = get_dahua_live_feed(
                device.domain,
                device.username,
                device.password,
                0  # Test first camera
            )
            if live_feed:
                print(f"   Live Feed: SUCCESS")
                print(f"   Stream URL: {live_feed.get('stream_url', 'N/A')}")
                print(f"   Camera Info: {live_feed.get('camera_info', 'N/A')}")
                print(f"   Status: {live_feed.get('status', 'N/A')}")
            else:
                print(f"   Live Feed: FAILED")
        except Exception as e:
            print(f"   Live Feed Error: {e}")
        
        # Update device status based on tests
        try:
            device.check_status()
            print(f"\n   Device Status Updated: {device.status}")
        except Exception as e:
            print(f"   Status Update Error: {e}")
    
    print(f"\n{'='*60}")
    print("TEST COMPLETE")
    print(f"{'='*60}")
    
    # Summary
    online_count = CCTVDevice.objects.filter(status='online').count()
    offline_count = CCTVDevice.objects.filter(status='offline').count()
    unknown_count = CCTVDevice.objects.filter(status='unknown').count()
    
    print(f"\nSUMMARY:")
    print(f"  Online: {online_count}")
    print(f"  Offline: {offline_count}")
    print(f"  Unknown: {unknown_count}")
    print(f"  Total: {devices.count()}")

if __name__ == "__main__":
    test_all_devices()
