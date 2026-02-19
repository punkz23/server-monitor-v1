#!/usr/bin/env python
"""Test firewall authentication from correct IP address"""

import os
import sys
import django
import requests
from urllib.parse import urljoin

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_firewall_authentication():
    """Test different authentication methods"""
    
    FIREWALL_HOST = "192.168.253.2"
    FIREWALL_PORT = 4444
    USERNAME = "francois_ignacio"
    PASSWORD = "iCFIzzl1QjmwBV80@"
    
    base_url = f"https://{FIREWALL_HOST}:{FIREWALL_PORT}"
    
    print("Testing Firewall Authentication")
    print("=" * 50)
    print(f"Firewall: {FIREWALL_HOST}:{FIREWALL_PORT}")
    print(f"Username: {USERNAME}")
    print(f"Source IP: 192.168.253.100 (your IP)")
    print()
    
    # Disable SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Test 1: Direct API authentication
    print("1. Testing Direct API Authentication...")
    session = requests.Session()
    session.verify = False
    
    login_xml = f"""<Request>
    <Authentication>
        <Username>{USERNAME}</Username>
        <Password>{PASSWORD}</Password>
    </Authentication>
</Request>"""
    
    try:
        response = session.post(
            f"{base_url}/webconsole/APIController",
            data={'reqxml': login_xml},
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code == 200 and 'Authentication Failure' not in response.text:
            print("   ✓ Direct API authentication successful!")
            return test_api_endpoints(session, base_url)
        else:
            print("   ✗ Direct API authentication failed")
            
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 2: Form-based authentication
    print("\n2. Testing Form-Based Authentication...")
    try:
        # Get login page first
        login_page = session.get(base_url, timeout=10)
        print(f"   Login page status: {login_page.status_code}")
        
        # Submit form
        form_data = {
            "username": USERNAME,
            "password": PASSWORD,
            "mode": "1"
        }
        
        response = session.post(base_url, data=form_data, timeout=10, allow_redirects=True)
        print(f"   Form login status: {response.status_code}")
        
        if response.status_code == 200 and 'name="username"' not in response.text:
            print("   ✓ Form authentication successful!")
            return test_api_endpoints(session, base_url)
        else:
            print("   ✗ Form authentication failed")
            
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 3: Try with different headers
    print("\n3. Testing with Different Headers...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        session.headers.update(headers)
        
        response = session.post(
            f"{base_url}/webconsole/APIController",
            data={'reqxml': login_xml},
            timeout=10
        )
        
        print(f"   Status with headers: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
    except Exception as e:
        print(f"   ✗ Error with headers: {e}")
    
    # Test 4: Check if IP is blocked
    print("\n4. Testing IP Access...")
    try:
        test_response = requests.get(base_url, timeout=5, verify=False)
        print(f"   Basic access status: {test_response.status_code}")
        
        if test_response.status_code == 200:
            print("   ✓ IP can reach firewall")
        else:
            print(f"   ✗ IP access blocked or firewall down")
            
    except Exception as e:
        print(f"   ✗ IP access error: {e}")
    
    print("\n5. Recommendations:")
    print("   - Check firewall admin console for API access settings")
    print("   - Verify 192.168.253.100 is in allowed IP list")
    print("   - Check if API is enabled on firewall")
    print("   - Try accessing from firewall's local network")
    print("   - Check firewall logs for authentication attempts")
    
    return None

def test_api_endpoints(session, base_url):
    """Test API endpoints after successful authentication"""
    print("\n✓ Testing API Endpoints...")
    
    endpoints = [
        ('System Status', '<Request><Get><SystemStatus></SystemStatus></Get></Request>'),
        ('Interfaces', '<Request><Get><Interface></Interface></Get></Request>'),
        ('ARP Table', '<Request><Get><ARPTable></ARPTable></Get></Request>'),
        ('DHCP Leases', '<Request><Get><DHCPLeaseTable></DHCPLeaseTable></Get></Request>')
    ]
    
    results = {}
    
    for name, xml_request in endpoints:
        try:
            response = session.get(
                f"{base_url}/webconsole/APIController",
                params={'reqxml': xml_request},
                timeout=10
            )
            
            if response.status_code == 200:
                if 'Authentication Failure' not in response.text:
                    print(f"   ✓ {name}: Success")
                    results[name] = response.text
                else:
                    print(f"   ✗ {name}: Authentication failed")
            else:
                print(f"   ✗ {name}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ✗ {name}: Error - {e}")
    
    return results

if __name__ == "__main__":
    test_firewall_authentication()
