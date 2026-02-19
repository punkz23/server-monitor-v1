#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.models import NetworkDevice
import requests
import urllib3

# Get the firewall device
firewall = NetworkDevice.objects.filter(device_type=NetworkDevice.TYPE_FIREWALL).first()
if firewall:
    print(f'Testing manual login for: {firewall.name} ({firewall.ip_address})')
    print('Please verify the credentials and try logging in manually through the web interface.')
    print(f'URL: https://{firewall.ip_address}:{firewall.api_port}/webconsole/')
    print(f'Username: {firewall.api_username}')
    print(f'Password: {"[REDACTED]" if firewall.api_token else "NOT SET"}')
    
    # Check if the credentials work by testing a simple system status request
    # with different authentication approaches
    
    base_url = f"https://{firewall.ip_address}:{firewall.api_port}/"
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    print("\n=== Testing if there might be an API user issue ===")
    
    # Try to access the API without authentication to see what error we get
    try:
        session = requests.Session()
        session.verify = False
        
        # Test unauthenticated access
        response = session.get(
            f"{base_url}webconsole/APIController?reqxml=<Request><Get><SystemStatus></SystemStatus></Get></Request>",
            timeout=10
        )
        
        print(f"Unauthenticated access status: {response.status_code}")
        print(f"Unauthenticated response: {response.text[:300]}...")
        
        # The response shows "Authentication Failure" which means the API endpoint is working
        # but we need proper credentials
        
    except Exception as e:
        print(f"Error testing unauthenticated access: {e}")
    
    print("\n=== Possible Issues ===")
    print("1. The credentials might be incorrect")
    print("2. The user might not have API access permissions")
    print("3. The API might be disabled")
    print("4. There might be IP restrictions on API access")
    print("5. The firewall might require a different authentication method")
    
    print("\n=== Recommendations ===")
    print("1. Verify the credentials work by logging into the web interface manually")
    print("2. Check if there's a separate API user or API key generation")
    print("3. Look in the firewall admin for API access settings")
    print("4. Check if the user has appropriate permissions for API access")
    print("5. Verify the firewall allows API access from your IP")

else:
    print('No firewall device found')
