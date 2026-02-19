#!/usr/bin/env python
"""Cyberoam firewall API scanner for network device discovery"""

import os
import sys
import django
import json
import requests
from urllib.parse import urljoin
from ipaddress import ip_address, ip_network
from typing import Dict, List, Optional

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.services.network_scanner import NetworkScanner
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CyberoamAPIClient:
    """Client for Cyberoam firewall API"""
    
    def __init__(self, host, port, username, password, verify_ssl=False):
        self.base_url = f"https://{host}:{port}/"
        self.session = requests.Session()
        self.session.verify = verify_ssl
        self.auth_token = None
        
        # Disable SSL warnings
        if not verify_ssl:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        self.login(username, password)
    
    def login(self, username, password):
        """Login to Cyberoam and get authentication token"""
        try:
            # First, get the login page to establish session
            login_page = self.session.get(self.base_url, timeout=10)
            
            # Cyberoam typically uses form-based login
            login_data = {
                'username': username,
                'password': password,
                'mode': '1'  # Standard login mode
            }
            
            # Submit login form
            response = self.session.post(
                self.base_url,
                data=login_data,
                timeout=10,
                allow_redirects=True
            )
            
            if response.status_code == 200:
                # Try to access a protected page to verify login
                api_test = self.session.get(
                    urljoin(self.base_url, 'userportal/webapi'),
                    timeout=5
                )
                
                if api_test.status_code == 200:
                    self.auth_token = True
                    logger.info("Successfully authenticated with Cyberoam")
                    return True
            
            logger.error("Authentication failed")
            return False
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    def get_arp_table(self):
        """Get ARP table - try different Cyberoam endpoints"""
        endpoints = [
            'userportal/webapi?reqxml=<Request><Get><ARPTable></ARPTable></Get></Request>',
            'webconsole/APIController?reqxml=<Request><Get><ARPTable></ARPTable></Get></Request>',
            'api/arp_table',
            'userportal/api/arp',
            'webapi/arp'
        ]
        
        for endpoint in endpoints:
            try:
                response = self.session.get(
                    urljoin(self.base_url, endpoint),
                    timeout=10
                )
                
                if response.status_code == 200 and response.text.strip().startswith('<?xml'):
                    logger.info(f"Successfully got ARP table from: {endpoint}")
                    return response.text
                elif response.status_code == 200:
                    logger.info(f"Got response from: {endpoint} - {response.text[:100]}...")
                    
            except Exception as e:
                logger.debug(f"Failed to get ARP from {endpoint}: {e}")
        
        return None
    
    def get_dhcp_leases(self):
        """Get DHCP lease table"""
        endpoints = [
            'userportal/webapi?reqxml=<Request><Get><DHCPLeaseTable></DHCPLeaseTable></Get></Request>',
            'webconsole/APIController?reqxml=<Request><Get><DHCPLeaseTable></DHCPLeaseTable></Get></Request>',
            'api/dhcp_leases',
            'userportal/api/dhcp'
        ]
        
        for endpoint in endpoints:
            try:
                response = self.session.get(
                    urljoin(self.base_url, endpoint),
                    timeout=10
                )
                
                if response.status_code == 200 and response.text.strip().startswith('<?xml'):
                    logger.info(f"Successfully got DHCP leases from: {endpoint}")
                    return response.text
                elif response.status_code == 200:
                    logger.info(f"Got response from: {endpoint} - {response.text[:100]}...")
                    
            except Exception as e:
                logger.debug(f"Failed to get DHCP from {endpoint}: {e}")
        
        return None
    
    def get_live_connections(self):
        """Get live connections"""
        endpoints = [
            'userportal/webapi?reqxml=<Request><Get><LiveConnection></LiveConnection></Get></Request>',
            'webconsole/APIController?reqxml=<Request><Get><LiveConnection></LiveConnection></Get></Request>',
            'api/live_connections',
            'userportal/api/connections'
        ]
        
        for endpoint in endpoints:
            try:
                response = self.session.get(
                    urljoin(self.base_url, endpoint),
                    timeout=10
                )
                
                if response.status_code == 200 and response.text.strip().startswith('<?xml'):
                    logger.info(f"Successfully got live connections from: {endpoint}")
                    return response.text
                elif response.status_code == 200:
                    logger.info(f"Got response from: {endpoint} - {response.text[:100]}...")
                    
            except Exception as e:
                logger.debug(f"Failed to get connections from {endpoint}: {e}")
        
        return None

class CyberoamNetworkScanner:
    """Scanner that uses Cyberoam Firewall API to discover network devices"""
    
    def __init__(self, firewall_host, firewall_port, username, password):
        self.firewall_host = firewall_host
        self.firewall_port = firewall_port
        self.username = username
        self.password = password
        self.client = None
        self.local_scanner = NetworkScanner()
        
    def connect(self):
        """Connect to Cyberoam firewall"""
        try:
            self.client = CyberoamAPIClient(
                host=self.firewall_host,
                port=self.firewall_port,
                username=self.username,
                password=self.password,
                verify_ssl=False
            )
            logger.info(f"Successfully connected to Cyberoam firewall at {self.firewall_host}:{self.firewall_port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Cyberoam firewall: {e}")
            return False
    
    def scan_network(self, target_network="172.10.10.0/24"):
        """Scan network using Cyberoam API"""
        if not self.connect():
            return []
        
        all_devices = []
        
        # Try to get ARP table
        logger.info("Attempting to get ARP table...")
        arp_response = self.client.get_arp_table()
        if arp_response:
            arp_devices = self._parse_xml_response(arp_response, 'arp')
            all_devices.extend(arp_devices)
        
        # Try to get DHCP leases
        logger.info("Attempting to get DHCP leases...")
        dhcp_response = self.client.get_dhcp_leases()
        if dhcp_response:
            dhcp_devices = self._parse_xml_response(dhcp_response, 'dhcp')
            all_devices.extend(dhcp_devices)
        
        # Try to get live connections
        logger.info("Attempting to get live connections...")
        conn_response = self.client.get_live_connections()
        if conn_response:
            conn_devices = self._parse_xml_response(conn_response, 'connections')
            all_devices.extend(conn_devices)
        
        # Filter and deduplicate
        filtered_devices = self._filter_and_deduplicate(all_devices, target_network)
        
        logger.info(f"Found {len(filtered_devices)} devices in {target_network}")
        return filtered_devices
    
    def _parse_xml_response(self, xml_string, source_type):
        """Parse XML response from Cyberoam"""
        import xml.etree.ElementTree as ET
        
        devices = []
        
        try:
            root = ET.fromstring(xml_string)
            
            # Look for different possible XML structures
            for child in root:
                if child.tag in ['ARPTable', 'ARP_Entry', 'ARP']:
                    for entry in child:
                        if entry.tag in ['ARPEntry', 'Entry', 'ARP_Entry']:
                            device = self._extract_device_info(entry, source_type)
                            if device:
                                devices.append(device)
                
                elif child.tag == 'Get' and child.get('status') == 'success':
                    for subchild in child:
                        if subchild.tag in ['ARPTable', 'DHCPLeaseTable', 'LiveConnection']:
                            for entry in subchild:
                                if entry.tag in ['ARPEntry', 'Lease', 'Connection']:
                                    device = self._extract_device_info(entry, source_type)
                                    if device:
                                        devices.append(device)
            
            logger.debug(f"Parsed {len(devices)} devices from {source_type}")
            return devices
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse XML from {source_type}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing {source_type} response: {e}")
            return []
    
    def _extract_device_info(self, entry, source_type):
        """Extract device information from XML entry"""
        try:
            device = {
                'ip_address': None,
                'mac_address': None,
                'hostname': None,
                'vendor': 'Unknown',
                'device_type': 'unknown',
                'source': source_type,
                'open_ports': {}
            }
            
            # Extract fields from XML entry
            for field in entry:
                tag_name = field.tag.lower()
                value = field.text or ''
                
                if tag_name in ['ipaddress', 'ip', 'ip_address']:
                    device['ip_address'] = value
                elif tag_name in ['macaddress', 'mac', 'mac_address']:
                    device['mac_address'] = value.upper() if value else None
                elif tag_name in ['hostname', 'name', 'clientname']:
                    device['hostname'] = value
            
            # Get vendor from MAC address
            if device['mac_address']:
                mac_prefix = device['mac_address'].replace('-', ':').upper()[:8]
                device['vendor'] = self.local_scanner.VENDOR_PREFIXES.get(mac_prefix, 'Unknown')
                device['device_type'] = self._identify_device_type(device['mac_address'])
            
            return device if device['ip_address'] else None
            
        except Exception as e:
            logger.debug(f"Error extracting device info: {e}")
            return None
    
    def _filter_and_deduplicate(self, devices, target_network):
        """Filter devices by network and remove duplicates"""
        try:
            network = ip_network(target_network, strict=False)
            unique_devices = {}
            
            for device in devices:
                ip = device.get('ip_address')
                if not ip:
                    continue
                
                # Check if IP is in target network
                try:
                    if ip_address(ip) not in network:
                        continue
                except ValueError:
                    continue
                
                # Use IP as key to deduplicate
                if ip not in unique_devices:
                    unique_devices[ip] = device
                else:
                    # Merge information if we have more details
                    existing = unique_devices[ip]
                    if not existing.get('mac_address') and device.get('mac_address'):
                        existing['mac_address'] = device['mac_address']
                        existing['vendor'] = device['vendor']
                        existing['device_type'] = device['device_type']
                    if not existing.get('hostname') and device.get('hostname'):
                        existing['hostname'] = device['hostname']
            
            return list(unique_devices.values())
            
        except Exception as e:
            logger.error(f"Error filtering devices: {e}")
            return []
    
    def _identify_device_type(self, mac):
        """Identify device type from MAC address"""
        if not mac:
            return 'unknown'
        
        mac_prefix = mac.replace('-', ':').upper()[:8]
        vendor = self.local_scanner.VENDOR_PREFIXES.get(mac_prefix, '')
        
        from monitor.models import NetworkDevice
        
        if vendor in ['Apple', 'Samsung', 'Huawei', 'Xiaomi']:
            return NetworkDevice.TYPE_MOBILE
        elif vendor in ['HP', 'Lexmark', 'Brother', 'Canon']:
            return NetworkDevice.TYPE_PRINTER
        elif vendor in ['Cisco']:
            return NetworkDevice.TYPE_SWITCH
        elif vendor in ['VMware', 'VirtualBox', 'Microsoft Hyper-V']:
            return NetworkDevice.TYPE_PC
        
        return NetworkDevice.TYPE_UNKNOWN

def main():
    """Main scanning function"""
    # Configuration
    FIREWALL_HOST = "192.168.253.2"
    FIREWALL_PORT = 4443
    USERNAME = "francois_ignacio"
    PASSWORD = "iCFIzzl1QjmwBV80@"
    
    print("Cyberoam Firewall Network Scanner")
    print("=" * 50)
    print(f"Target Network: 172.10.10.0/24")
    print(f"Firewall: {FIREWALL_HOST}:{FIREWALL_PORT}")
    print()
    
    # Create scanner
    scanner = CyberoamNetworkScanner(FIREWALL_HOST, FIREWALL_PORT, USERNAME, PASSWORD)
    
    # Scan network
    devices = scanner.scan_network("172.10.10.0/24")
    
    # Display results
    print(f"\nFound {len(devices)} devices on 172.10.10.0/24:")
    print("=" * 80)
    
    for i, device in enumerate(devices, 1):
        print(f"Device {i}:")
        print(f"  IP Address: {device['ip_address']}")
        print(f"  MAC Address: {device['mac_address'] or 'Unknown'}")
        print(f"  Hostname: {device['hostname'] or 'Unknown'}")
        print(f"  Vendor: {device['vendor']}")
        print(f"  Device Type: {device['device_type']}")
        print(f"  Source: {device['source']}")
        print("-" * 40)
    
    # Save results to JSON file
    with open('cyberoam_scan_results.json', 'w') as f:
        json.dump(devices, f, indent=2)
    
    print(f"\nResults saved to cyberoam_scan_results.json")
    print(f"Scan completed. Found {len(devices)} devices on 172.10.10.0/24")

if __name__ == "__main__":
    main()
