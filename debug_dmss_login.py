#!/usr/bin/env python
"""
Debug DMSS Login Issues
"""

import os
import sys
import django
import requests

# Set up Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.dmss_integration import DMSSClient

def test_dmss_login():
    """Test DMSS login with debugging"""
    
    print("=" * 60)
    print("DMSS LOGIN DEBUG")
    print("=" * 60)
    
    client = DMSSClient()
    
    # Test 1: Check API endpoints
    print("\n1. Testing DMSS API endpoints...")
    print(f"   Base URL: {client.base_url}")
    print(f"   API URL: {client.api_url}")
    
    # Test 2: Test basic connectivity
    print("\n2. Testing basic connectivity...")
    try:
        response = requests.get(client.base_url, timeout=10)
        print(f"   Base URL Status: {response.status_code}")
    except Exception as e:
        print(f"   Base URL Error: {e}")
    
    # Test 3: Test API endpoint
    print("\n3. Testing API endpoint...")
    try:
        response = requests.get(f"{client.api_url}/login", timeout=10)
        print(f"   API URL Status: {response.status_code}")
    except Exception as e:
        print(f"   API URL Error: {e}")
    
    # Test 4: Test with sample credentials (if provided)
    print("\n4. Testing login process...")
    print("   To test with your credentials:")
    print("   1. Enter your DMSS username and password in the web form")
    print("   2. Check browser network tab for API calls")
    print("   3. Look for error details in Django logs")
    
    # Test 5: Check possible API endpoints
    print("\n5. Possible DMSS API endpoints to try:")
    endpoints = [
        "https://dmss.dahua.com/api/v1/login",
        "https://dmss.dahua.com/api/v2/login", 
        "https://dmss.dahua.com/api/login",
        "https://dmss.dahua.com/mobile/api/login",
        "https://easy4ipcloud.com/api/login"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(endpoint, timeout=5)
            print(f"   {endpoint}: {response.status_code}")
        except:
            print(f"   {endpoint}: Failed")
    
    print("\n" + "=" * 60)
    print("DEBUGGING SUGGESTIONS:")
    print("=" * 60)
    print("1. Verify DMSS credentials are correct")
    print("2. Check if DMSS account is active")
    print("3. Try DMSS mobile app to confirm credentials work")
    print("4. Check network connectivity to dmss.dahua.com")
    print("5. Look for DMSS API documentation")
    print("6. Check if 2FA is enabled on DMSS account")

if __name__ == "__main__":
    test_dmss_login()
