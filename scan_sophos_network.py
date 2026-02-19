#!/usr/bin/env python
"""Script to scan devices on the 172.10.10.0/24 network using Sophos Firewall API"""

import os
import sys
import django
import json
from ipaddress import ip_address, ip_network
from typing import Dict, List, Optional

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.sophos import SophosXGS126Client
from monitor.sophos_xml_parser import SophosXMLParser
from monitor.services.network_scanner import NetworkScanner
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SophosNetworkScanner:
    """Scanner that uses Sophos Firewall API to discover network devices"""
    
    def __init__(self, firewall_host='192.168.253.2', firewall_port=4444, 
                 username='admin', password=None):
        """Initialize with firewall connection details"""
        self.firewall_host = firewall_host
        self.firewall_port = firewall_port
        self.username = username
        self.password = password
        self.client = None
        self.local_scanner = NetworkScanner()
        
    def connect(self):
        """Connect to Sophos firewall"""
        try:
            self.client = SophosXGS126Client(
                host=self.firewall_host,
                port=self.firewall_port,
                username=self.username,
                password=self.password,
                verify_ssl=False
            )
            logger.info(f"Successfully connected to Sophos firewall at {self.firewall_host}:{self.firewall_port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Sophos firewall: {e}")
            return False
    
    def scan_arp_table(self) -> List[Dict]:
        """Get ARP table from firewall"""
        if not self.client:
            raise Exception("Not connected to firewall")
        
        try:
            logger.info("Fetching ARP table from firewall...")
            arp_response = self.client.get_arp_table()
            
            if isinstance(arp_response, str) and arp_response.strip().startswith('<?xml'):
                arp_entries = SophosXMLParser.parse_arp_table(arp_response)
                devices = []
                
                for entry in arp_entries:
                    device = self._normalize_arp_entry(entry)
                    if device:
                        devices.append(device)
                
                logger.info(f"Found {len(devices)} devices in ARP table")
                return devices
            else:
                logger.warning(f"Unexpected ARP response format: {type(arp_response)}")
                return []
                
        except Exception as e:
            logger.error(f"Error scanning ARP table: {e}")
            return []
    
    def scan_dhcp_leases(self) -> List[Dict]:
        """Get DHCP lease table from firewall"""
        if not self.client:
            raise Exception("Not connected to firewall")
        
        try:
            logger.info("Fetching DHCP lease table from firewall...")
            dhcp_response = self.client.get_dhcp_leases()
            
            if isinstance(dhcp_response, str) and dhcp_response.strip().startswith('<?xml'):
                dhcp_leases = SophosXMLParser.parse_dhcp_leases(dhcp_response)
                devices = []
                
                for lease in dhcp_leases:
                    device = self._normalize_dhcp_lease(lease)
                    if device:
                        devices.append(device)
                
                logger.info(f"Found {len(devices)} DHCP leases")
                return devices
            else:
                logger.warning(f"Unexpected DHCP response format: {type(dhcp_response)}")
                return []
                
        except Exception as e:
            logger.error(f"Error scanning DHCP leases: {e}")
            return []
    
    def scan_network_hosts(self) -> List[Dict]:
        """Get network hosts from firewall"""
        if not self.client:
            raise Exception("Not connected to firewall")
        
        try:
            logger.info("Fetching network hosts from firewall...")
            hosts_response = self.client.get_network_hosts()
            
            if isinstance(hosts_response, str) and hosts_response.strip().startswith('<?xml'):
                hosts = SophosXMLParser.parse_network_hosts(hosts_response)
                devices = []
                
                for host in hosts:
                    device = self._normalize_network_host(host)
                    if device:
                        devices.append(device)
                
                logger.info(f"Found {len(devices)} network hosts")
                return devices
            else:
                logger.warning(f"Unexpected hosts response format: {type(hosts_response)}")
                return []
                
        except Exception as e:
            logger.error(f"Error scanning network hosts: {e}")
            return []
    
    def scan_live_connections(self) -> List[Dict]:
        """Get live connection list from firewall"""
        if not self.client:
            raise Exception("Not connected to firewall")
        
        try:
            logger.info("Fetching live connection list from firewall...")
            
            # Use the existing authenticated session from the client
            connection_xml = """<Request>
    <get>
        <ConnectionList/>
    </get>
</Request>"""
            
            connections_response = self.client.session.post(
                f"https://{self.firewall_host}:{self.firewall_port}/webconsole/APIController",
                data=connection_xml,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                verify=False
            )
            
            if connections_response.status_code == 200:
                connections_xml = connections_response.text
                logger.info(f"Full XML response from ConnectionList:")
                logger.info(connections_xml[:1000])  # Log first 1000 chars
                
                # Check if we got HTML (login page) instead of XML
                if connections_xml.strip().startswith('<!DOCTYPE') or connections_xml.strip().startswith('<html'):
                    logger.warning("Got HTML response instead of XML - authentication issue")
                    return []
                
                # Parse the connection list XML
                devices = self._parse_connection_list(connections_xml)
                logger.info(f"Found {len(devices)} devices from live connections")
                return devices
            else:
                logger.warning(f"ConnectionList request failed with status: {connections_response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error scanning live connections: {e}")
            return []
    
    def _parse_connection_list(self, xml_content: str) -> List[Dict]:
        """Parse connection list XML to extract unique devices"""
        devices = {}
        
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_content)
            
            # Look for connection entries
            for conn in root.findall('.//Connection'):
                src_ip = conn.get('srcip') or conn.get('SourceIP')
                dst_ip = conn.get('dstip') or conn.get('DestIP')
                
                # Add source IPs as devices (these are local network devices)
                if src_ip and self._is_valid_ip(src_ip):
                    if src_ip not in devices:
                        devices[src_ip] = {
                            'ip_address': src_ip,
                            'mac_address': None,
                            'hostname': None,
                            'vendor': 'Unknown',
                            'device_type': 'unknown',
                            'source': 'live_connections',
                            'open_ports': {}
                        }
                
                # Also add destination IPs if they're in local network
                if dst_ip and self._is_valid_ip(dst_ip) and dst_ip.startswith('192.168.'):
                    if dst_ip not in devices:
                        devices[dst_ip] = {
                            'ip_address': dst_ip,
                            'mac_address': None,
                            'hostname': None,
                            'vendor': 'Unknown',
                            'device_type': 'unknown',
                            'source': 'live_connections',
                            'open_ports': {}
                        }
            
            return list(devices.values())
            
        except Exception as e:
            logger.error(f"Error parsing connection list XML: {e}")
            return []
        """Get active connections from firewall"""
        if not self.client:
            raise Exception("Not connected to firewall")
        
        try:
            logger.info("Fetching active connections from firewall...")
            connections_response = self.client.get_active_connections()
            
            if isinstance(connections_response, str) and connections_response.strip().startswith('<?xml'):
                connections = SophosXMLParser.parse_firewall_sessions(connections_response)
                # Extract unique IPs from connections
                devices = []
                
                if isinstance(connections, dict):
                    # Parse connection details if available
                    for key, value in connections.items():
                        if 'ip' in key.lower() and isinstance(value, str):
                            if self._is_valid_ip(value):
                                device = {
                                    'ip_address': value,
                                    'mac_address': None,
                                    'hostname': None,
                                    'vendor': 'Unknown',
                                    'device_type': 'unknown',
                                    'source': 'active_connections',
                                    'open_ports': []
                                }
                                devices.append(device)
                
                logger.info(f"Found {len(devices)} unique IPs from active connections")
                return devices
            else:
                logger.warning(f"Unexpected connections response format: {type(connections_response)}")
                return []
                
        except Exception as e:
            logger.error(f"Error scanning active connections: {e}")
            return []
    
    def scan_all_sources(self, target_network="172.10.10.0/24") -> List[Dict]:
        """Scan all available sources and merge results"""
        if not self.connect():
            return []
        
        all_devices = []
        
        # Scan from different sources
        arp_devices = self.scan_arp_table()
        dhcp_devices = self.scan_dhcp_leases()
        host_devices = self.scan_network_hosts()
        connection_devices = self.scan_live_connections()  # Use new method
        
        # Combine all devices
        all_devices.extend(arp_devices)
        all_devices.extend(dhcp_devices)
        all_devices.extend(host_devices)
        all_devices.extend(connection_devices)
        
        # Filter by target network and remove duplicates
        filtered_devices = self._filter_and_deduplicate(all_devices, target_network)
        
        logger.info(f"Total unique devices found in {target_network}: {len(filtered_devices)}")
        return filtered_devices
    
    def _normalize_arp_entry(self, entry: Dict) -> Optional[Dict]:
        """Normalize ARP entry to standard device format"""
        try:
            ip = entry.get('ipaddress') or entry.get('ip') or entry.get('ip_address')
            mac = entry.get('macaddress') or entry.get('mac') or entry.get('mac_address')
            
            if not ip or not self._is_valid_ip(ip):
                return None
            
            device = {
                'ip_address': ip,
                'mac_address': mac.upper() if mac else None,
                'hostname': entry.get('hostname') or entry.get('name'),
                'vendor': self._get_vendor_from_mac(mac) if mac else 'Unknown',
                'device_type': self._identify_device_type(mac) if mac else 'unknown',
                'source': 'arp_table',
                'open_ports': {}
            }
            
            return device
        except Exception as e:
            logger.debug(f"Error normalizing ARP entry: {e}")
            return None
    
    def _normalize_dhcp_lease(self, lease: Dict) -> Optional[Dict]:
        """Normalize DHCP lease to standard device format"""
        try:
            ip = lease.get('ipaddress') or lease.get('ip') or lease.get('ip_address')
            mac = lease.get('macaddress') or lease.get('mac') or lease.get('mac_address')
            hostname = lease.get('hostname') or lease.get('clientname') or lease.get('name')
            
            if not ip or not self._is_valid_ip(ip):
                return None
            
            device = {
                'ip_address': ip,
                'mac_address': mac.upper() if mac else None,
                'hostname': hostname,
                'vendor': self._get_vendor_from_mac(mac) if mac else 'Unknown',
                'device_type': self._identify_device_type(mac) if mac else 'unknown',
                'source': 'dhcp_lease',
                'open_ports': {}
            }
            
            return device
        except Exception as e:
            logger.debug(f"Error normalizing DHCP lease: {e}")
            return None
    
    def _normalize_network_host(self, host: Dict) -> Optional[Dict]:
        """Normalize network host to standard device format"""
        try:
            ip = host.get('ipaddress') or host.get('ip') or host.get('ip_address')
            mac = host.get('macaddress') or host.get('mac') or host.get('mac_address')
            hostname = host.get('hostname') or host.get('name')
            
            if not ip or not self._is_valid_ip(ip):
                return None
            
            device = {
                'ip_address': ip,
                'mac_address': mac.upper() if mac else None,
                'hostname': hostname,
                'vendor': self._get_vendor_from_mac(mac) if mac else 'Unknown',
                'device_type': self._identify_device_type(mac) if mac else 'unknown',
                'source': 'network_hosts',
                'open_ports': {}
            }
            
            return device
        except Exception as e:
            logger.debug(f"Error normalizing network host: {e}")
            return None
    
    def _filter_and_deduplicate(self, devices: List[Dict], target_network: str) -> List[Dict]:
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
                    
                    # Combine sources
                    sources = existing.get('sources', [])
                    if isinstance(existing.get('source'), str):
                        sources.append(existing['source'])
                    if isinstance(device.get('source'), str) and device['source'] not in sources:
                        sources.append(device['source'])
                    existing['sources'] = sources
            
            return list(unique_devices.values())
            
        except Exception as e:
            logger.error(f"Error filtering and deduplicating devices: {e}")
            return []
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Check if IP address is valid"""
        try:
            ip_address(ip)
            return True
        except ValueError:
            return False
    
    def _get_vendor_from_mac(self, mac: str) -> str:
        """Get vendor from MAC address using local scanner's vendor database"""
        if not mac:
            return 'Unknown'
        
        mac_prefix = mac.replace('-', ':').upper()[:8]
        return self.local_scanner.VENDOR_PREFIXES.get(mac_prefix, 'Unknown')
    
    def _identify_device_type(self, mac: str) -> str:
        """Identify device type from MAC address"""
        if not mac:
            return 'unknown'
        
        mac_prefix = mac.replace('-', ':').upper()[:8]
        vendor = self.local_scanner.VENDOR_PREFIXES.get(mac_prefix, '')
        
        # Import NetworkDevice model for device types
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

def update_database(devices: List[Dict]):
    """Update database with discovered devices"""
    from django.utils import timezone
    from monitor.models import NetworkDevice
    created_count = 0
    updated_count = 0
    
    print(f"\nUpdating database with {len(devices)} devices...")
    
    for device_info in devices:
        try:
            # Check if device exists
            existing_device = None
            
            if device_info.get('mac_address'):
                existing_device = NetworkDevice.objects.filter(
                    mac_address=device_info['mac_address']
                ).first()
            
            if not existing_device:
                existing_device = NetworkDevice.objects.filter(
                    ip_address=device_info['ip_address']
                ).first()
            
            if existing_device:
                # Update existing device
                existing_device.ip_address = device_info['ip_address']
                existing_device.mac_address = device_info['mac_address']
                existing_device.vendor = device_info['vendor']
                existing_device.hostname = device_info['hostname']
                existing_device.device_type = device_info['device_type']
                existing_device.last_seen = timezone.now()
                existing_device.is_active = True
                existing_device.save()
                updated_count += 1
                print(f"Updated: {existing_device.name} ({existing_device.ip_address})")
            else:
                # Create new device
                device_name = device_info['hostname'] or f"Device-{device_info['ip_address'].split('.')[-1]}"
                
                # Ensure name is unique
                base_name = device_name
                counter = 1
                while NetworkDevice.objects.filter(name=device_name).exists():
                    device_name = f"{base_name}-{counter}"
                    counter += 1
                
                new_device = NetworkDevice.objects.create(
                    name=device_name,
                    device_type=device_info['device_type'],
                    ip_address=device_info['ip_address'],
                    mac_address=device_info['mac_address'],
                    vendor=device_info['vendor'],
                    hostname=device_info['hostname'],
                    auto_discovered=True,
                    is_active=True,
                )
                created_count += 1
                print(f"Created: {new_device.name} ({new_device.ip_address})")
                
        except Exception as e:
            print(f"Error processing device {device_info.get('ip_address', 'unknown')}: {e}")
    
    # Mark old devices as inactive
    recent_cutoff = timezone.now() - timezone.timedelta(hours=24)
    inactive_count = NetworkDevice.objects.filter(
        auto_discovered=True,
        last_seen__lt=recent_cutoff,
        is_active=True
    ).update(is_active=False)
    
    if inactive_count > 0:
        print(f"Marked {inactive_count} devices as inactive")
    
    print(f"\nDatabase update complete:")
    print(f"  Created: {created_count} devices")
    print(f"  Updated: {updated_count} devices")
    print(f"  Marked inactive: {inactive_count} devices")

def main():
    """Main scanning function"""
    # Configuration - update these with your actual firewall details
    FIREWALL_HOST = "192.168.253.2"  # The actual firewall IP address
    FIREWALL_PORT = 4444  # Correct API port from database
    USERNAME = "francois_ignacio"  # Update with actual username
    PASSWORD = "iCFIzzl1QjmwBV80@"  # Update with actual password
    
    print("Sophos Firewall Network Scanner")
    print("=" * 50)
    print(f"Firewall: {FIREWALL_HOST}:{FIREWALL_PORT}")
    print()
    
    # Create scanner
    scanner = SophosNetworkScanner(FIREWALL_HOST, FIREWALL_PORT, USERNAME, PASSWORD)
    
    # Scan real networks
    networks_to_scan = ["192.168.253.0/24", "192.168.254.0/24"]
    all_devices = []
    
    for network in networks_to_scan:
        print(f"Scanning network: {network}")
        devices = scanner.scan_all_sources(network)
        all_devices.extend(devices)
        print(f"Found {len(devices)} devices on {network}")
    
    # Remove duplicates by IP address
    unique_devices = {}
    for device in all_devices:
        ip = device['ip_address']
        if ip not in unique_devices:
            unique_devices[ip] = device
        else:
            # Merge information if device exists from multiple sources
            existing = unique_devices[ip]
            if not existing.get('hostname') and device.get('hostname'):
                existing['hostname'] = device['hostname']
            if not existing.get('mac_address') and device.get('mac_address'):
                existing['mac_address'] = device['mac_address']
            if 'sources' not in existing:
                existing['sources'] = [existing.get('source', 'unknown')]
            if device.get('source') not in existing['sources']:
                existing['sources'].append(device['source'])
    
    unique_devices = list(unique_devices.values())
    
    # Display results
    print(f"\nFound {len(unique_devices)} unique devices:")
    print("=" * 80)
    
    for i, device in enumerate(unique_devices, 1):
        print(f"Device {i}:")
        print(f"  IP Address: {device['ip_address']}")
        print(f"  MAC Address: {device['mac_address'] or 'Unknown'}")
        print(f"  Hostname: {device['hostname'] or 'Unknown'}")
        print(f"  Vendor: {device['vendor']}")
        print(f"  Device Type: {device['device_type']}")
        print(f"  Source: {device.get('source', 'unknown')}")
        if 'sources' in device:
            print(f"  Sources: {', '.join(device['sources'])}")
        print("-" * 40)
    
    # Save results to JSON file
    with open('sophos_scan_results.json', 'w') as f:
        json.dump(unique_devices, f, indent=2)
    
    print(f"\nResults saved to sophos_scan_results.json")
    
    # Update database
    if unique_devices:
        response = input(f"\nUpdate database with {len(unique_devices)} devices? (y/N): ")
        if response.lower() in ['y', 'yes']:
            update_database(unique_devices)
        else:
            print("Database update cancelled.")
    
    print(f"\nScan completed. Found {len(unique_devices)} unique devices.")

if __name__ == "__main__":
    main()
