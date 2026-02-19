#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.models import NetworkDevice
from monitor.sophos import SophosXGS126Client
import requests
from urllib.parse import urljoin

# Get the firewall device
firewall = NetworkDevice.objects.filter(device_type=NetworkDevice.TYPE_FIREWALL).first()
if firewall:
    print(f'Testing firewall: {firewall.name} ({firewall.ip_address})')
    print(f'API Port: {firewall.api_port}')
    print(f'API Username: {firewall.api_username}')
    
    # Test different authentication approaches
    base_url = f"https://{firewall.ip_address}:{firewall.api_port}/"
    
    print(f"\nTesting connection to: {base_url}")
    
    # Test 1: Basic connectivity
    try:
        session = requests.Session()
        session.verify = False
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Try to access login page
        response = session.get(f"{base_url}webconsole/", timeout=10)
        print(f"Login page status: {response.status_code}")
        print(f"Login page content preview: {response.text[:500]}...")
        
        # Look for form fields in the login page
        if 'username' in response.text.lower():
            print("Found username field in login page")
        
        # Test different login data
        login_attempts = [
            {
                "username": firewall.api_username,
                "password": firewall.api_token,
                "mode": "191"
            },
            {
                "username": firewall.api_username,
                "password": firewall.api_token,
            },
            {
                "username": firewall.api_username,
                "password": firewall.api_token,
                "ajax": "1",
                "action": "login"
            }
        ]
        
        for i, form_data in enumerate(login_attempts):
            print(f"\n--- Login Attempt {i+1} ---")
            print(f"Form data: {form_data}")
            
            login_response = session.post(
                f"{base_url}webconsole/",
                data=form_data,
                timeout=10,
                allow_redirects=True
            )
            
            print(f"Login response status: {login_response.status_code}")
            print(f"Login response content preview: {login_response.text[:500]}...")
            
            # Test API access after login
            if login_response.status_code == 200:
                api_test = session.get(
                    f"{base_url}webconsole/APIController?reqxml=<Request><Get><SystemStatus></SystemStatus></Get></Request>",
                    timeout=10
                )
                print(f"API test status: {api_test.status_code}")
                if api_test.text.startswith('<?xml'):
                    print("API access successful!")
                    print(f"API response preview: {api_test.text[:300]}...")
                    
                    # Check for authentication status in XML
                    if 'Authentication Failure' in api_test.text:
                        print("Still getting authentication failure")
                    elif 'SystemStatus' in api_test.text:
                        print("Successfully got system status!")
                        break
                else:
                    print(f"API response: {api_test.text[:300]}...")
    
    except Exception as e:
        print(f"Error during testing: {e}")
else:
    print('No firewall device found')
