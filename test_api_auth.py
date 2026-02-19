#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.models import NetworkDevice
import requests
import urllib3
from urllib.parse import urljoin
import base64

# Get the firewall device
firewall = NetworkDevice.objects.filter(device_type=NetworkDevice.TYPE_FIREWALL).first()
if firewall:
    print(f'Testing firewall: {firewall.name} ({firewall.ip_address})')
    
    base_url = f"https://{firewall.ip_address}:{firewall.api_port}/"
    
    # Disable SSL warnings
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    session = requests.Session()
    session.verify = False
    
    # Try different authentication methods
    
    print("\n=== Method 1: Basic Auth ===")
    try:
        # Try basic authentication
        auth_string = f"{firewall.api_username}:{firewall.api_token}"
        auth_b64 = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {auth_b64}',
            'Accept': 'application/xml, text/xml, */*'
        }
        
        response = session.get(
            f"{base_url}webconsole/APIController?reqxml=<Request><Get><SystemStatus></SystemStatus></Get></Request>",
            headers=headers,
            timeout=10
        )
        
        print(f"Basic auth status: {response.status_code}")
        print(f"Basic auth response: {response.text[:300]}...")
        
    except Exception as e:
        print(f"Basic auth error: {e}")
    
    print("\n=== Method 2: Direct API login ===")
    try:
        # Try direct API login
        login_xml = f"""<Request>
    <Authentication>
        <Username>{firewall.api_username}</Username>
        <Password>{firewall.api_token}</Password>
    </Authentication>
</Request>"""
        
        response = session.post(
            f"{base_url}webconsole/APIController",
            data={'reqxml': login_xml},
            timeout=10
        )
        
        print(f"Direct API login status: {response.status_code}")
        print(f"Direct API login response: {response.text[:300]}...")
        
    except Exception as e:
        print(f"Direct API login error: {e}")
    
    print("\n=== Method 3: Form-based login with different mode ===")
    try:
        # Get login page first
        login_page = session.get(f"{base_url}webconsole/", timeout=10)
        
        # Try with different mode values
        modes_to_try = ['191', '1', '0', '2', 'api']
        
        for mode in modes_to_try:
            print(f"\nTrying mode: {mode}")
            
            form_data = {
                'username': firewall.api_username,
                'password': firewall.api_token,
                'mode': mode,
                'loginbutton': 'Login'
            }
            
            login_response = session.post(
                f"{base_url}webconsole/",
                data=form_data,
                timeout=10,
                allow_redirects=False  # Don't follow redirects to see what happens
            )
            
            print(f"  Login status: {login_response.status_code}")
            print(f"  Location: {login_response.headers.get('Location', 'None')}")
            
            # Test API access
            api_test = session.get(
                f"{base_url}webconsole/APIController?reqxml=<Request><Get><SystemStatus></SystemStatus></Get></Request>",
                timeout=10
            )
            
            if 'Authentication Failure' not in api_test.text:
                print(f"  SUCCESS with mode {mode}!")
                print(f"  API response: {api_test.text[:200]}...")
                break
            else:
                print(f"  Still failed with mode {mode}")
    
    except Exception as e:
        print(f"Form-based login error: {e}")
    
    print("\n=== Method 4: Check API endpoints ===")
    try:
        # Try different API endpoints
        endpoints = [
            "webconsole/APIController",
            "api/",
            "webconsole/api/",
            "APIController"
        ]
        
        for endpoint in endpoints:
            print(f"\nTrying endpoint: {endpoint}")
            
            response = session.get(
                f"{base_url}{endpoint}?reqxml=<Request><Get><SystemStatus></SystemStatus></Get></Request>",
                timeout=10
            )
            
            print(f"  Status: {response.status_code}")
            if response.text and len(response.text) > 10:
                print(f"  Response: {response.text[:200]}...")
    
    except Exception as e:
        print(f"API endpoint test error: {e}")

else:
    print('No firewall device found')
