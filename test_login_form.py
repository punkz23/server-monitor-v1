#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.models import NetworkDevice
import requests
from bs4 import BeautifulSoup
import urllib3
from urllib.parse import urljoin

# Get the firewall device
firewall = NetworkDevice.objects.filter(device_type=NetworkDevice.TYPE_FIREWALL).first()
if firewall:
    print(f'Testing firewall: {firewall.name} ({firewall.ip_address})')
    
    base_url = f"https://{firewall.ip_address}:{firewall.api_port}/"
    
    # Disable SSL warnings
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    session = requests.Session()
    session.verify = False
    
    # Get the login page and parse the form
    try:
        response = session.get(f"{base_url}webconsole/", timeout=10)
        print(f"Login page status: {response.status_code}")
        
        if response.status_code == 200:
            # Parse the HTML to find the login form
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the login form
            login_form = soup.find('form')
            if login_form:
                print(f"Found login form with action: {login_form.get('action', 'N/A')}")
                print(f"Form method: {login_form.get('method', 'N/A')}")
                
                # Find all input fields
                inputs = login_form.find_all('input')
                print(f"Found {len(inputs)} input fields:")
                
                form_data = {}
                for input_field in inputs:
                    field_name = input_field.get('name')
                    field_type = input_field.get('type', 'text')
                    field_value = input_field.get('value', '')
                    
                    print(f"  - {field_name} ({field_type}): '{field_value}'")
                    
                    if field_name:
                        if field_name == 'username':
                            form_data[field_name] = firewall.api_username
                        elif field_name == 'password':
                            form_data[field_name] = firewall.api_token
                        elif field_name and field_value:
                            form_data[field_name] = field_value
                
                print(f"\nForm data to submit: {form_data}")
                
                # Submit the form
                form_action = login_form.get('action', '')
                if not form_action.startswith('/'):
                    form_action = f"/webconsole/{form_action}"
                
                submit_url = urljoin(base_url, form_action)
                print(f"Submitting to: {submit_url}")
                
                login_response = session.post(
                    submit_url,
                    data=form_data,
                    timeout=10,
                    allow_redirects=True
                )
                
                print(f"Login response status: {login_response.status_code}")
                print(f"Final URL after login: {login_response.url}")
                
                # Test API access
                api_test = session.get(
                    f"{base_url}webconsole/APIController?reqxml=<Request><Get><SystemStatus></SystemStatus></Get></Request>",
                    timeout=10
                )
                
                print(f"API test status: {api_test.status_code}")
                if api_test.text.startswith('<?xml'):
                    print("API response:")
                    print(api_test.text[:500])
                    
                    if 'Authentication Failure' not in api_test.text:
                        print("SUCCESS: Authentication worked!")
                    else:
                        print("FAILED: Still getting authentication failure")
                else:
                    print(f"API response: {api_test.text[:300]}...")
            else:
                print("No login form found")
                
                # Look for any forms on the page
                all_forms = soup.find_all('form')
                print(f"Total forms found: {len(all_forms)}")
                for i, form in enumerate(all_forms):
                    print(f"Form {i+1}: {form.get('action', 'N/A')} - {form.get('method', 'N/A')}")
        
    except Exception as e:
        print(f"Error: {e}")
else:
    print('No firewall device found')
