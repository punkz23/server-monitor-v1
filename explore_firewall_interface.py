#!/usr/bin/env python
"""Explore firewall web interface after login to find available APIs"""

import os
import sys
import django
import requests
from urllib.parse import urljoin
import re

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def explore_firewall():
    """Explore firewall interface after login"""
    
    FIREWALL_HOST = "192.168.253.2"
    FIREWALL_PORT = 4443
    USERNAME = "francois_ignacio"
    PASSWORD = "iCFIzzl1QjmwBV80@"
    
    base_url = f"https://{FIREWALL_HOST}:{FIREWALL_PORT}"
    session = requests.Session()
    session.verify = False
    
    # Disable SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    print("Exploring Cyberoam Firewall Interface")
    print("=" * 50)
    
    try:
        # Step 1: Get login page
        print("1. Getting login page...")
        login_page = session.get(base_url, timeout=10)
        print(f"   Login page status: {login_page.status_code}")
        
        # Step 2: Login
        print("2. Logging in...")
        login_data = {
            'username': USERNAME,
            'password': PASSWORD,
            'mode': '1'
        }
        
        login_response = session.post(base_url, data=login_data, timeout=10, allow_redirects=True)
        print(f"   Login response status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            # Check if we're logged in by looking for login form
            if 'name="username"' not in login_response.text:
                print("   ✓ Login successful!")
                
                # Save the logged-in page
                with open('firewall_logged_in.html', 'w') as f:
                    f.write(login_response.text)
                print("   Saved logged-in page to firewall_logged_in.html")
                
                # Step 3: Look for API endpoints in the page
                print("3. Searching for API endpoints...")
                
                # Look for common API patterns
                api_patterns = [
                    r'["\']([^"\']*api[^"\']*)["\']',
                    r'["\']([^"\']*webapi[^"\']*)["\']',
                    r'["\']([^"\']*xml[^"\']*)["\']',
                    r'["\']([^"\']*rpc[^"\']*)["\']',
                    r'action=["\']([^"\']*)["\']',
                    r'url:\s*["\']([^"\']*)["\']'
                ]
                
                found_apis = set()
                for pattern in api_patterns:
                    matches = re.findall(pattern, login_response.text, re.IGNORECASE)
                    for match in matches:
                        if 'api' in match.lower() or 'xml' in match.lower() or 'rpc' in match.lower():
                            found_apis.add(match)
                
                if found_apis:
                    print(f"   Found potential API endpoints:")
                    for api in sorted(found_apis):
                        print(f"     - {api}")
                else:
                    print("   No obvious API endpoints found in page source")
                
                # Step 4: Look for JavaScript files that might contain API info
                print("4. Searching for JavaScript files...")
                js_patterns = [
                    r'href=["\']([^"\']*\.js[^"\']*)["\']',
                    r'src=["\']([^"\']*\.js[^"\']*)["\']'
                ]
                
                js_files = set()
                for pattern in js_patterns:
                    matches = re.findall(pattern, login_response.text, re.IGNORECASE)
                    for match in matches:
                        if match.startswith('/'):
                            js_files.add(match)
                        elif not match.startswith('http'):
                            js_files.add('/' + match)
                
                print(f"   Found {len(js_files)} JavaScript files")
                
                # Test some common JavaScript files
                test_js_files = [
                    '/javascript/common_min.js',
                    '/javascript/validation/UserPortalLogin.js',
                    '/javascript/jQueryYUI.js',
                    '/javascript/react-combo.min.js'
                ]
                
                for js_file in test_js_files:
                    try:
                        js_url = urljoin(base_url, js_file)
                        js_response = session.get(js_url, timeout=5)
                        if js_response.status_code == 200:
                            print(f"   ✓ Got {js_file}")
                            
                            # Look for API endpoints in JavaScript
                            for pattern in api_patterns:
                                matches = re.findall(pattern, js_response.text, re.IGNORECASE)
                                for match in matches:
                                    if 'api' in match.lower() or 'xml' in match.lower():
                                        print(f"     Found API in {js_file}: {match}")
                        else:
                            print(f"   ✗ Failed to get {js_file}: {js_response.status_code}")
                    except Exception as e:
                        print(f"   ✗ Error getting {js_file}: {e}")
                
                # Step 5: Try common API endpoints
                print("5. Testing common API endpoints...")
                common_endpoints = [
                    '/webconsole/APIController',
                    '/userportal/webapi',
                    '/api/v1',
                    '/api',
                    '/xmlrpc',
                    '/rpc2',
                    '/webapi',
                    '/api/v2',
                    '/rest/api',
                    '/rest/v1'
                ]
                
                for endpoint in common_endpoints:
                    try:
                        api_url = urljoin(base_url, endpoint)
                        test_response = session.get(api_url, timeout=5)
                        print(f"   {endpoint}: {test_response.status_code}")
                        
                        if test_response.status_code == 200:
                            # Save successful API response
                            with open(f'api_response_{endpoint.replace("/", "_")}.txt', 'w') as f:
                                f.write(test_response.text)
                            print(f"     Saved response to api_response_{endpoint.replace('/', '_')}.txt")
                            
                    except Exception as e:
                        print(f"   {endpoint}: Error - {e}")
                
                # Step 6: Try to find network device pages
                print("6. Looking for network device pages...")
                network_patterns = [
                    r'["\']([^"\']*arp[^"\']*)["\']',
                    r'["\']([^"\']*dhcp[^"\']*)["\']',
                    r'["\']([^"\']*host[^"\']*)["\']',
                    r'["\']([^"\']*device[^"\']*)["\']',
                    r'["\']([^"\']*client[^"\']*)["\']'
                ]
                
                found_network_pages = set()
                for pattern in network_patterns:
                    matches = re.findall(pattern, login_response.text, re.IGNORECASE)
                    for match in matches:
                        found_network_pages.add(match)
                
                if found_network_pages:
                    print(f"   Found network-related pages:")
                    for page in sorted(found_network_pages):
                        print(f"     - {page}")
                        
                        # Try to access these pages
                        try:
                            page_url = urljoin(base_url, page)
                            page_response = session.get(page_url, timeout=5)
                            if page_response.status_code == 200:
                                print(f"       ✓ Accessible: {page_response.status_code}")
                                with open(f'network_page_{page.replace("/", "_")}.html', 'w') as f:
                                    f.write(page_response.text)
                        except Exception as e:
                            print(f"       ✗ Error accessing {page}: {e}")
                
            else:
                print("   ✗ Login failed - still showing login form")
                
        else:
            print(f"   ✗ Login failed with status: {login_response.status_code}")
            
    except Exception as e:
        print(f"✗ Error during exploration: {e}")

if __name__ == "__main__":
    explore_firewall()
