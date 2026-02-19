#!/usr/bin/env python3
"""
TP-Link Deco Network Scanner
Scans the 172.10.10.0/24 network through the Deco device web interface
"""

import sys
import os
import json
import logging
import requests
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import re

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
import django
django.setup()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DecoNetworkScanner:
    """Scanner for TP-Link Deco mesh router network"""
    
    def __init__(self, deco_ip, username, password):
        self.deco_ip = deco_ip
        self.username = username
        self.password = password
        self.base_urls = [
            f"http://{deco_ip}",
            f"https://{deco_ip}",
            f"http://{deco_ip}:80",
            f"https://{deco_ip}:443",
            f"http://{deco_ip}:8080",
            f"https://{deco_ip}:8443"
        ]
        self.session = requests.Session()
        self.session.verify = False  # Deco often uses self-signed certs
        self.authenticated = False
        
        # Disable SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def login(self):
        """Login to Deco web interface"""
        try:
            logger.info(f"Attempting to login to Deco at {self.deco_ip}")
            
            # First test basic connectivity
            if not self._test_connectivity():
                logger.error("Cannot reach Deco device - network connectivity issue")
                return False
            
            # Try each base URL
            for base_url in self.base_urls:
                logger.info(f"Trying base URL: {base_url}")
                self.current_base_url = base_url
                
                # Try common Deco login endpoints
                login_endpoints = [
                    "/",
                    "/login.html", 
                    "/webpages/login.html",
                    "/cgi-bin/luci",
                    "/tplink/login.html"
                ]
                
                for endpoint in login_endpoints:
                    try:
                        url = urljoin(base_url, endpoint)
                        logger.info(f"Trying login endpoint: {url}")
                        
                        response = self.session.get(url, timeout=5)
                        
                        if response.status_code == 200:
                            # Check if this is a login page
                            if any(keyword in response.text.lower() for keyword in ['login', 'password', 'username', 'signin']):
                                logger.info(f"Found login page at: {url}")
                                
                                # Parse the login form
                                soup = BeautifulSoup(response.text, 'html.parser')
                                
                                # Try different login methods
                                if self._try_form_login(response, soup):
                                    return True
                                elif self._try_api_login():
                                    return True
                                else:
                                    logger.warning(f"Login form found but authentication failed at {url}")
                                    
                    except requests.exceptions.RequestException as e:
                        logger.debug(f"Failed to access {url}: {e}")
                        continue
            
            logger.error("No suitable login endpoint found")
            return False
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    def _test_connectivity(self):
        """Test basic connectivity to the Deco device"""
        try:
            logger.info("Testing basic connectivity to Deco device...")
            
            # Try ping-like connectivity test
            for base_url in self.base_urls:
                try:
                    url = urljoin(base_url, "/")
                    response = self.session.get(url, timeout=3)
                    
                    if response.status_code in [200, 301, 302, 403, 404]:
                        logger.info(f"Deco device responds at: {base_url}")
                        return True
                        
                except requests.exceptions.RequestException:
                    continue
            
            logger.error("No response from Deco device on any port/protocol")
            return False
            
        except Exception as e:
            logger.error(f"Connectivity test failed: {e}")
            return False
    
    def _try_form_login(self, response, soup):
        """Try form-based login"""
        try:
            # Find login form
            forms = soup.find_all('form')
            
            for form in forms:
                action = form.get('action', '')
                method = form.get('method', 'POST').upper()
                
                # Find username and password fields
                username_field = None
                password_field = None
                
                for input_tag in form.find_all('input'):
                    input_type = input_tag.get('type', '').lower()
                    input_name = input_tag.get('name', '').lower()
                    
                    if input_type == 'email' or 'username' in input_name or 'user' in input_name or 'email' in input_name:
                        username_field = input_tag.get('name')
                    elif input_type == 'password' or 'password' in input_name:
                        password_field = input_tag.get('name')
                
                if username_field and password_field:
                    logger.info(f"Found login form with fields: {username_field}, {password_field}")
                    
                    # Prepare login data
                    login_data = {
                        username_field: self.username,
                        password_field: self.password
                    }
                    
                    # Add any hidden fields
                    for hidden in form.find_all('input', type='hidden'):
                        login_data[hidden.get('name')] = hidden.get('value', '')
                    
                    # Submit login
                    login_url = urljoin(self.base_url, action) if action else response.url
                    
                    if method == 'POST':
                        login_response = self.session.post(login_url, data=login_data, timeout=10)
                    else:
                        login_response = self.session.get(login_url, params=login_data, timeout=10)
                    
                    # Check if login was successful
                    if self._check_login_success(login_response):
                        logger.info("Form login successful!")
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Form login failed: {e}")
            return False
    
    def _try_api_login(self):
        """Try API-based login (common for newer Deco models)"""
        try:
            # Try common Deco API endpoints
            api_endpoints = [
                "/cgi-bin/luci/rpc/auth",
                "/data/login.json",
                "/api/login",
                "/rpc/login",
                "/webapi/auth"
            ]
            
            for endpoint in api_endpoints:
                try:
                    url = urljoin(self.current_base_url, endpoint)
                    
                    # Try different API formats
                    api_payloads = [
                        {"username": self.username, "password": self.password},
                        {"user": self.username, "pass": self.password},
                        {"email": self.username, "password": self.password},
                        {"method": "login", "params": {"username": self.username, "password": self.password}}
                    ]
                    
                    for payload in api_payloads:
                        response = self.session.post(url, json=payload, timeout=5)
                        
                        if response.status_code == 200:
                            try:
                                result = response.json()
                                if result.get('success') or result.get('status') == 'success' or 'token' in result:
                                    logger.info(f"API login successful via {endpoint}")
                                    return True
                            except ValueError:
                                pass
                    
                except requests.exceptions.RequestException:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"API login failed: {e}")
            return False
    
    def _check_login_success(self, response):
        """Check if login was successful"""
        # Check for common success indicators
        success_indicators = [
            'dashboard', 'home', 'overview', 'devices', 'clients',
            'logout', 'signout', 'main', 'status'
        ]
        
        failure_indicators = [
            'login failed', 'invalid', 'incorrect', 'error', 'unauthorized'
        ]
        
        response_text = response.text.lower()
        
        # Check for failure indicators first
        for indicator in failure_indicators:
            if indicator in response_text:
                return False
        
        # Check for success indicators
        for indicator in success_indicators:
            if indicator in response_text:
                return True
        
        # Check status code and content
        return response.status_code == 200 and len(response.text) > 1000
    
    def get_connected_devices(self):
        """Get list of connected devices from Deco"""
        if not self.authenticated:
            if not self.login():
                return []
        
        devices = []
        
        try:
            # Try different device list endpoints
            device_endpoints = [
                "/",
                "/webpages/home.html",
                "/webpages/devices.html", 
                "/webpages/clients.html",
                "/cgi-bin/luci/rpc/getDevices",
                "/data/devices.json",
                "/api/devices",
                "/api/clients"
            ]
            
            for endpoint in device_endpoints:
                try:
                    url = urljoin(self.base_url, endpoint)
                    logger.info(f"Trying devices endpoint: {url}")
                    
                    response = self.session.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        # Try to parse device information
                        parsed_devices = self._parse_devices(response, endpoint)
                        if parsed_devices:
                            devices.extend(parsed_devices)
                            logger.info(f"Found {len(parsed_devices)} devices from {endpoint}")
                            
                except requests.exceptions.RequestException as e:
                    logger.debug(f"Failed to access {url}: {e}")
                    continue
            
            # Remove duplicates
            unique_devices = []
            seen_macs = set()
            seen_ips = set()
            
            for device in devices:
                mac = device.get('mac', '').lower()
                ip = device.get('ip', '')
                
                if mac and mac not in seen_macs:
                    seen_macs.add(mac)
                    unique_devices.append(device)
                elif ip and ip not in seen_ips:
                    seen_ips.add(ip)
                    unique_devices.append(device)
            
            logger.info(f"Total unique devices found: {len(unique_devices)}")
            return unique_devices
            
        except Exception as e:
            logger.error(f"Failed to get connected devices: {e}")
            return []
    
    def _parse_devices(self, response, endpoint):
        """Parse device information from response"""
        devices = []
        
        try:
            # Try JSON parsing first
            if 'json' in response.headers.get('content-type', '').lower():
                try:
                    data = response.json()
                    
                    # Handle different JSON structures
                    if isinstance(data, list):
                        for item in data:
                            device = self._extract_device_info(item)
                            if device:
                                devices.append(device)
                    elif isinstance(data, dict):
                        # Look for device lists in common keys
                        for key in ['devices', 'clients', 'deviceList', 'clientList']:
                            if key in data and isinstance(data[key], list):
                                for item in data[key]:
                                    device = self._extract_device_info(item)
                                    if device:
                                        devices.append(device)
                        
                        # Also check if the dict itself is a device
                        if 'ip' in data or 'mac' in data:
                            device = self._extract_device_info(data)
                            if device:
                                devices.append(device)
                
                except ValueError:
                    pass
            
            # Try HTML parsing
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for device tables
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows[1:]:  # Skip header
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        device = self._extract_device_from_cells(cells)
                        if device:
                            devices.append(device)
            
            # Look for device cards/divs
            device_divs = soup.find_all(['div', 'li'], class_=re.compile(r'device|client|host', re.I))
            for div in device_divs:
                device = self._extract_device_from_div(div)
                if device:
                    devices.append(device)
            
        except Exception as e:
            logger.error(f"Error parsing devices from {endpoint}: {e}")
        
        return devices
    
    def _extract_device_info(self, item):
        """Extract device information from JSON item"""
        device = {}
        
        # Common field names
        field_mappings = {
            'ip': ['ip', 'ip_address', 'ipaddr', 'address', 'host_ip'],
            'mac': ['mac', 'mac_address', 'macaddr', 'hwaddr', 'hardware_address'],
            'name': ['name', 'hostname', 'device_name', 'client_name', 'host_name'],
            'type': ['type', 'device_type', 'category', 'model'],
            'status': ['status', 'state', 'online', 'connected']
        }
        
        for field, possible_names in field_mappings.items():
            for name in possible_names:
                if name in item and item[name]:
                    device[field] = str(item[name])
                    break
        
        # Only return if we have at least IP or MAC
        if device.get('ip') or device.get('mac'):
            return device
        
        return None
    
    def _extract_device_from_cells(self, cells):
        """Extract device information from table cells"""
        device = {}
        
        # Try to identify IP, MAC, and name from cell content
        for i, cell in enumerate(cells):
            text = cell.get_text(strip=True)
            
            # IP address pattern
            if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', text):
                device['ip'] = text
            
            # MAC address pattern  
            elif re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', text):
                device['mac'] = text
            
            # Device name (usually not IP/MAC)
            elif len(text) > 3 and not re.match(r'^\d', text) and i < 3:
                if not device.get('name'):
                    device['name'] = text
        
        return device if device.get('ip') or device.get('mac') else None
    
    def _extract_device_from_div(self, div):
        """Extract device information from div element"""
        device = {}
        text = div.get_text(strip=True)
        
        # Look for IP and MAC in the text
        ip_match = re.search(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', text)
        mac_match = re.search(r'\b([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})\b', text)
        
        if ip_match:
            device['ip'] = ip_match.group()
        if mac_match:
            device['mac'] = mac_match.group()
        
        # Try to get name from title or first text element
        title = div.get('title') or div.find(['h1', 'h2', 'h3', 'h4'])
        if title:
            device['name'] = title.get_text(strip=True) if hasattr(title, 'get_text') else str(title)
        
        return device if device.get('ip') or device.get('mac') else None
    
    def scan_network(self):
        """Main scanning function"""
        logger.info("Starting Deco network scan...")
        logger.info(f"Target network: 172.10.10.0/24")
        logger.info(f"Deco device: {self.deco_ip}")
        
        # Get connected devices
        devices = self.get_connected_devices()
        
        # Filter for devices in the target network
        target_devices = []
        for device in devices:
            ip = device.get('ip', '')
            if ip.startswith('172.10.10.'):
                target_devices.append(device)
        
        logger.info(f"Found {len(target_devices)} devices in 172.10.10.0/24 network")
        
        # Save results
        results = {
            'scan_time': datetime.now().isoformat(),
            'target_network': '172.10.10.0/24',
            'deco_device': self.deco_ip,
            'total_devices_found': len(target_devices),
            'devices': target_devices
        }
        
        output_file = 'deco_scan_results.json'
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved to {output_file}")
        
        # Display results
        print(f"\nDeco Network Scanner Results")
        print(f"==========================")
        print(f"Target Network: 172.10.10.0/24")
        print(f"Deco Device: {self.deco_ip}")
        print(f"Devices Found: {len(target_devices)}")
        print(f"")
        
        for device in target_devices:
            print(f"Device: {device.get('name', 'Unknown')}")
            print(f"  IP: {device.get('ip', 'N/A')}")
            print(f"  MAC: {device.get('mac', 'N/A')}")
            print(f"  Type: {device.get('type', 'N/A')}")
            print(f"  Status: {device.get('status', 'N/A')}")
            print(f"")
        
        return results

def main():
    """Main function"""
    # Deco device configuration
    DECO_IP = "172.10.10.101"
    USERNAME = "doffit2025@gmail.com"
    PASSWORD = "itUser@doff"
    
    # Create and run scanner
    scanner = DecoNetworkScanner(DECO_IP, USERNAME, PASSWORD)
    results = scanner.scan_network()
    
    print(f"\nScan completed. Found {results['total_devices_found']} devices on 172.10.10.0/24")

if __name__ == "__main__":
    main()
