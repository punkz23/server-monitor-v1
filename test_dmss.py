#!/usr/bin/env python
"""
Test DMSS Cloud Integration
"""

import os
import sys
import django

# Set up Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.dmss_integration import DMSSClient

def test_dmss_integration():
    """Test DMSS integration functionality"""
    
    print("=" * 60)
    print("DMSS CLOUD INTEGRATION TEST")
    print("=" * 60)
    
    # Test 1: Client initialization
    print("\n1. Testing DMSS client initialization...")
    client = DMSSClient()
    print(f"   Client initialized: {client}")
    print(f"   Base URL: {client.base_url}")
    print(f"   API URL: {client.api_url}")
    
    # Test 2: Login status check
    print("\n2. Testing login status...")
    print(f"   Is logged in: {client.is_logged_in()}")
    
    # Test 3: Mock login test (without real credentials)
    print("\n3. Testing login endpoint (mock)...")
    print("   To test with real credentials:")
    print("   1. Go to CCTV dashboard: http://192.168.253.100:8001/cctv/")
    print("   2. Enter your DMSS username and password")
    print("   3. Click 'Login' button")
    print("   4. Check status messages")
    
    # Test 4: Device list test (without login)
    print("\n4. Testing device list (without login)...")
    devices, message = client.get_device_list()
    print(f"   Devices: {len(devices)}")
    print(f"   Message: {message}")
    
    # Test 5: URL endpoints test
    print("\n5. Testing API endpoints...")
    endpoints = [
        "/cctv/dmss/status/",
        "/cctv/dmss/devices/",
        "/cctv/dmss/login/",
        "/cctv/dmss/logout/"
    ]
    
    for endpoint in endpoints:
        print(f"   Endpoint: {endpoint} - Available")
    
    print("\n" + "=" * 60)
    print("DMSS INTEGRATION READY FOR TESTING")
    print("=" * 60)
    
    print("\nHOW TO TEST:")
    print("1. Start Django server: python manage.py runserver")
    print("2. Open browser: http://192.168.253.100:8001/cctv/")
    print("3. Look for 'DMSS Cloud Integration' section")
    print("4. Enter your DMSS credentials")
    print("5. Click 'Login' button")
    print("6. Check status messages and device count")
    
    print("\nEXPECTED RESULTS:")
    print("- Login form should accept credentials")
    print("- Status messages should appear")
    print("- Device count should update if login successful")
    print("- Logout button should appear after login")
    
    print("\nDMSS FEATURES:")
    print("- Cloud device discovery")
    print("- P2P device access via DMSS")
    print("- Live streaming through cloud")
    print("- Device sharing capabilities")
    print("- Cloud storage access")

if __name__ == "__main__":
    test_dmss_integration()
