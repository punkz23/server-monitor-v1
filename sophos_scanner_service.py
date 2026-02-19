#!/usr/bin/env python
"""Updated Network Scanner Service using Sophos Firewall"""

import os
import sys
import django
import logging
from typing import Dict, List, Optional

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.sophos import SophosXGS126Client
from monitor.sophos_xml_parser import SophosXMLParser
from monitor.models import NetworkDevice
from django.utils import timezone

logger = logging.getLogger(__name__)

class SophosNetworkScanner:
    """Primary network scanner using Sophos Firewall API"""
    
    def __init__(self, firewall_host='192.168.253.2', firewall_port=4444):
        """Initialize with firewall connection details"""
        self.firewall_host = firewall_host
        self.firewall_port = firewall_port
        self.client = None
        
    def connect(self, username='admin', password=None):
        """Connect to Sophos firewall"""
        try:
            self.client = SophosXGS126Client(
                host=self.firewall_host,
                port=self.firewall_port,
                username=username,
                password=password,
                verify_ssl=False
            )
            logger.info(f"Successfully connected to Sophos firewall at {self.firewall_host}:{self.firewall_port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Sophos firewall: {e}")
            return False
    
    def scan_network(self, network_range: str = None) -> List[Dict]:
        """Scan network using Sophos firewall (ignores network_range parameter)"""
        if not self.client:
            logger.error("Not connected to firewall")
            return []
        
        all_devices = []
        
        try:
            # Scan ARP table
            logger.info("Fetching ARP table from firewall...")
            arp_response = self.client.get_arp_table()
            
            if isinstance(arp_response, str) and arp_response.strip().startswith('<?xml'):
                arp_entries = SophosXMLParser.parse_arp_table(arp_response)
                
                for entry in arp_entries:
                    device = self._normalize_device(entry, 'arp')
                    if device and self._is_valid_device(device):
                        all_devices.append(device)
                
                logger.info(f"Found {len(all_devices)} devices in ARP table")
            
            # Scan DHCP leases for additional hostname info
            logger.info("Fetching DHCP leases from firewall...")
            dhcp_response = self.client.get_dhcp_leases()
            
            if isinstance(dhcp_response, str) and dhcp_response.strip().startswith('<?xml'):
                dhcp_leases = SophosXMLParser.parse_dhcp_leases(dhcp_response)
                
                # Merge hostname info from DHCP
                dhcp_map = {lease['ip']: lease for lease in dhcp_leases if lease.get('ip')}
                
                for device in all_devices:
                    ip = device['ip_address']
                    if ip in dhcp_map:
                        dhcp_lease = dhcp_map[ip]
                        if dhcp_lease.get('hostname') and not device.get('hostname'):
                            device['hostname'] = dhcp_lease['hostname']
                        if dhcp_lease.get('mac') and not device.get('mac_address'):
                            device['mac_address'] = dhcp_lease['mac']
                
                logger.info(f"Merged DHCP hostname information")
            
        except Exception as e:
            logger.error(f"Error scanning network: {e}")
        
        return all_devices
    
    def _normalize_device(self, entry: Dict, source: str) -> Optional[Dict]:
        """Normalize firewall entry to device format"""
        try:
            ip = entry.get('ip') or entry.get('ipaddress')
            mac = entry.get('mac') or entry.get('macaddress')
            
            if not ip:
                return None
            
            # Skip virtualization networks
            if ip.startswith('192.168.56.') or ip.startswith('172.10.10.'):
                return None
            
            return {
                'ip_address': ip,
                'mac_address': mac or '',
                'hostname': entry.get('hostname', ''),
                'vendor': entry.get('vendor', 'Unknown'),
                'device_type': self._identify_device_type(entry),
                'open_ports': {},  # Sophos doesn't provide port info
            }
        except Exception as e:
            logger.error(f"Error normalizing device: {e}")
            return None
    
    def _is_valid_device(self, device: Dict) -> bool:
        """Check if device is valid and should be included"""
        ip = device.get('ip_address', '')
        
        # Skip invalid IPs
        if not ip or ip == '0.0.0.0':
            return False
        
        # Skip virtualization networks
        if ip.startswith('192.168.56.') or ip.startswith('172.10.10.'):
            return False
        
        # Skip multicast and special addresses
        if ip.startswith('224.') or ip.startswith('239.') or ip.startswith('255.'):
            return False
        
        return True
    
    def _identify_device_type(self, device_info: Dict) -> str:
        """Identify device type based on available information"""
        hostname = device_info.get('hostname', '').lower()
        mac = device_info.get('mac', '').upper()
        ip = device_info.get('ip', '') or device_info.get('ipaddress', '')
        
        # Check MAC vendor prefixes
        if mac.startswith(('00:50:56', '00:0C:29')):  # VMware
            return NetworkDevice.TYPE_PC
        elif mac.startswith('08:00:27'):  # VirtualBox
            return NetworkDevice.TYPE_PC
        elif mac.startswith(('B8:27:EB', 'DC:A6:32', 'E4:5F:01')):  # Raspberry Pi
            return NetworkDevice.TYPE_PC
        elif mac.startswith(('00:1E:4F', '1C:CB:09', '3C:D9:2B')):  # HP
            return NetworkDevice.TYPE_PRINTER
        elif mac.startswith(('00:04:23', '00:0B:46')):  # Cisco
            return NetworkDevice.TYPE_SWITCH
        elif mac.startswith(('00:1A:2B', '28:CF:E9', 'A4:C1:38')):  # Apple
            return NetworkDevice.TYPE_MOBILE
        elif mac.startswith(('F0:18:98', 'E8:50:8B', 'AC:5D:9E')):  # Samsung
            return NetworkDevice.TYPE_MOBILE
        
        # Check hostname patterns
        if any(keyword in hostname for keyword in ['printer', 'hp', 'canon', 'epson', 'brother']):
            return NetworkDevice.TYPE_PRINTER
        elif any(keyword in hostname for keyword in ['router', 'firewall', 'gateway', 'fw']):
            return NetworkDevice.TYPE_ROUTER
        elif any(keyword in hostname for keyword in ['switch', 'sw']):
            return NetworkDevice.TYPE_SWITCH
        elif any(keyword in hostname for keyword in ['ap', 'access-point', 'wifi']):
            return NetworkDevice.TYPE_ACCESS_POINT
        elif any(keyword in hostname for keyword in ['phone', 'android', 'iphone']):
            return NetworkDevice.TYPE_MOBILE
        elif any(keyword in hostname for keyword in ['pc', 'desktop', 'laptop', 'computer']):
            return NetworkDevice.TYPE_PC
        
        # Check IP patterns
        if ip == '192.168.253.2':  # Sophos firewall
            return NetworkDevice.TYPE_FIREWALL
        
        return NetworkDevice.TYPE_UNKNOWN
    
    def get_local_networks(self) -> List[str]:
        """Return networks that Sophos firewall can see"""
        return ['192.168.253.0/24', '192.168.254.0/24', '192.168.1.0/24']
