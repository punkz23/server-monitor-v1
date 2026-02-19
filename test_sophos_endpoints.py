#!/usr/bin/env python
"""Test different Sophos API endpoints and ports"""

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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_endpoints():
    """Test different endpoints and ports"""
    
    FIREWALL_HOST = "192.168.253.2"
    USERNAME = "francois_ignacio"
    PASSWORD = "iCFIzzl1QjmwBV80@"
    
    # Test different ports
    ports = [443, 8443, 4443]
    
    # Test different endpoints
    endpoints = [
        "/webconsole/APIController",
        "/api/",
        "/webconsole/api/",
        "/api/v1/",
        "/xmlrpc",
        "/rpc2",
        "/webconsole/webapi/",
        "/sophos/api/"
    ]
    
    # Test different XML requests
    xml_requests = [
        "<Request><Get><SystemStatus></SystemStatus></Get></Request>",
        "<request><get><systemstatus></systemstatus></get></request>",
        "<XML><Get><SystemStatus></SystemStatus></Get></XML>",
        "reqxml=<Request><Get><SystemStatus></SystemStatus></Get></Request>",
        "<Request><SystemStatus/></Request>"
    ]
    
    print("Testing Sophos API Endpoints")
    print("=" * 60)
    
    for port in ports:
        print(f"\nTesting port {port}:")
        print("-" * 30)
        
        for endpoint in endpoints:
            base_url = f"https://{FIREWALL_HOST}:{port}"
            
            # Test basic connectivity
            try:
                response = requests.get(base_url + endpoint, timeout=5, verify=False)
                print(f"✓ {endpoint} - Status: {response.status_code}")
                
                # If we get a successful response, try XML API calls
                if response.status_code in [200, 302]:
                    print(f"  Testing XML API on {endpoint}...")
                    for xml_req in xml_requests[:2]:  # Test first 2 XML formats
                        try:
                            if "reqxml=" in endpoint:
                                test_url = base_url + endpoint + xml_req
                            else:
                                test_url = base_url + endpoint
                                params = {"reqxml": xml_req}
                            
                            if "reqxml=" in endpoint:
                                api_response = requests.get(test_url, timeout=5, verify=False)
                            else:
                                api_response = requests.get(test_url, params=params, timeout=5, verify=False)
                            
                            if api_response.status_code == 200:
                                print(f"    ✓ XML format worked: {xml_req[:50]}...")
                                print(f"      Response: {api_response.text[:200]}...")
                                return base_url + endpoint, xml_req
                            else:
                                print(f"    ✗ XML format failed: {api_response.status_code}")
                        except Exception as e:
                            print(f"    ✗ XML request error: {e}")
                            
            except requests.exceptions.ConnectTimeout:
                print(f"✗ {endpoint} - Timeout")
            except requests.exceptions.ConnectionError:
                print(f"✗ {endpoint} - Connection failed")
            except Exception as e:
                print(f"✗ {endpoint} - Error: {e}")
    
    # Try to access web interface directly to see what's available
    print(f"\nTrying to access web interface directly...")
    for port in ports:
        try:
            response = requests.get(f"https://{FIREWALL_HOST}:{port}", timeout=5, verify=False, allow_redirects=True)
            print(f"✓ Port {port} - Status: {response.status_code}")
            if response.status_code == 200:
                # Look for API clues in the HTML
                content = response.text.lower()
                if "api" in content:
                    print(f"  Found 'api' in content")
                if "xml" in content:
                    print(f"  Found 'xml' in content")
                if "rpc" in content:
                    print(f"  Found 'rpc' in content")
                    
                # Save the HTML for inspection
                with open(f"firewall_web_{port}.html", "w") as f:
                    f.write(response.text)
                print(f"  Saved HTML to firewall_web_{port}.html")
                
        except Exception as e:
            print(f"✗ Port {port} - Error: {e}")

if __name__ == "__main__":
    test_endpoints()
