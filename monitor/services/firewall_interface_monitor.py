"""Service for monitoring Sophos Firewall interfaces in real-time"""

import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
from monitor.sophos import SophosXGS126Client

logger = logging.getLogger(__name__)

class FirewallInterfaceMonitor:
    """Real-time monitor for Sophos Firewall interfaces"""
    
    def __init__(self, firewall_host='192.168.253.2', firewall_port=4444,
                 username='francois_ignacio', password='iCFIzzl1QjmwBV80@'):
        self.firewall_host = firewall_host
        self.firewall_port = firewall_port
        self.username = username
        self.password = password
        self.client = None
        
    def connect(self) -> bool:
        """Connect to Sophos firewall"""
        try:
            self.client = SophosXGS126Client(
                host=self.firewall_host,
                port=self.firewall_port,
                username=self.username,
                password=self.password,
                verify_ssl=False
            )
            logger.info(f"Connected to Sophos firewall at {self.firewall_host}:{self.firewall_port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Sophos firewall: {e}")
            return False
    
    def get_interfaces(self) -> List[Dict]:
        """Get current interface statistics from firewall"""
        if not self.client:
            if not self.connect():
                return []
        
        try:
            # Use the DHCP endpoint that returns interface statistics
            dhcp_response = self.client.get_dhcp_leases()
            
            if isinstance(dhcp_response, str) and dhcp_response.strip().startswith('<?xml'):
                interfaces = self._parse_interface_stats(dhcp_response)
                
                # Enhance interface data with additional details
                enhanced_interfaces = []
                for interface in interfaces:
                    enhanced_interface = interface.copy()
                    
                    # Add IP address based on interface name patterns
                    enhanced_interface['ip_address'] = self._get_interface_ip(interface['name'])
                    
                    # Add interface type based on name
                    enhanced_interface['type'] = self._get_interface_type(interface['name'])
                    
                    # Add speed based on interface type
                    enhanced_interface['speed'] = self._get_interface_speed(interface['name'])
                    
                    enhanced_interfaces.append(enhanced_interface)
                
                return enhanced_interfaces
            else:
                logger.warning(f"Unexpected response type: {type(dhcp_response)}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting interfaces: {e}")
            return []
    
    def _get_interface_ip(self, interface_name: str) -> str:
        """Get IP address for interface based on name patterns"""
        # Map interface names to their typical IP ranges
        interface_ip_map = {
            'WAN-PLDT': '192.168.253.2',
            'Internal': '192.168.253.1',
            'WIFI': '192.168.253.0/24',
            'GuestAP': '192.168.254.1',
            'HO PLDT3': '172.10.10.1',
            'Converge': '192.168.1.1',
            'Prepaid Wifi': '192.168.252.1',
            'Prepaid WifiGlobe': '192.168.251.1',
        }
        
        # For physical ports, assign based on port number
        if interface_name.startswith('Port'):
            port_num = interface_name.replace('Port', '').replace('F', '').replace('-test', '')
            if port_num.isdigit():
                return f'192.168.25{port_num.zfill(2)}.1' if int(port_num) < 10 else f'192.168.25{port_num}.1'
        
        return interface_ip_map.get(interface_name, 'N/A')
    
    def _get_interface_type(self, interface_name: str) -> str:
        """Determine interface type based on name"""
        if 'WAN' in interface_name or 'PLDT' in interface_name or 'Converge' in interface_name:
            return 'WAN'
        elif 'WIFI' in interface_name or 'GuestAP' in interface_name or 'Prepaid' in interface_name:
            return 'Wireless'
        elif interface_name.startswith('Port'):
            return 'Ethernet'
        elif interface_name == 'Internal':
            return 'LAN'
        else:
            return 'Unknown'
    
    def _get_interface_speed(self, interface_name: str) -> str:
        """Get interface speed based on type"""
        interface_type = self._get_interface_type(interface_name)
        
        speed_map = {
            'WAN': '1 Gbps',
            'Wireless': '1 Gbps',
            'Ethernet': '1 Gbps',
            'LAN': '1 Gbps'
        }
        
        return speed_map.get(interface_type, 'Unknown')
    
    def _parse_interface_stats(self, xml_content: str) -> List[Dict]:
        """Parse interface statistics from XML response"""
        interfaces = []
        
        try:
            root = ET.fromstring(xml_content)
            
            # Find all InterfaceStatistics entries
            interface_elements = root.findall('.//InterfaceStatistics')
            
            for interface_elem in interface_elements:
                name_elem = interface_elem.find('Name')
                usage_elem = interface_elem.find('Usage')
                transaction_id = interface_elem.get('transactionid', '')
                
                if name_elem is not None and usage_elem is not None:
                    interface = {
                        'name': name_elem.text,
                        'usage': int(usage_elem.text) if usage_elem.text.isdigit() else 0,
                        'transaction_id': transaction_id,
                        'status': 'active' if int(usage_elem.text or 0) > 0 else 'inactive'
                    }
                    interfaces.append(interface)
            
            logger.info(f"Parsed {len(interfaces)} interfaces from firewall")
            return interfaces
            
        except ET.ParseError as e:
            logger.error(f"Error parsing interface XML: {e}")
            return []
    
    def get_interface_changes(self, previous_interfaces: List[Dict]) -> Dict:
        """Compare current interfaces with previous state and return changes"""
        current_interfaces = self.get_interfaces()
        
        changes = {
            'added': [],
            'removed': [],
            'modified': [],
            'current': current_interfaces
        }
        
        # Create lookup dictionaries
        current_lookup = {iface['name']: iface for iface in current_interfaces}
        previous_lookup = {iface['name']: iface for iface in previous_interfaces}
        
        # Find added interfaces
        for name in current_lookup:
            if name not in previous_lookup:
                changes['added'].append(current_lookup[name])
        
        # Find removed interfaces
        for name in previous_lookup:
            if name not in current_lookup:
                changes['removed'].append(previous_lookup[name])
        
        # Find modified interfaces
        for name in current_lookup:
            if name in previous_lookup:
                current = current_lookup[name]
                previous = previous_lookup[name]
                
                if (current['usage'] != previous['usage'] or 
                    current['status'] != previous['status']):
                    changes['modified'].append({
                        'name': name,
                        'old_usage': previous['usage'],
                        'new_usage': current['usage'],
                        'old_status': previous['status'],
                        'new_status': current['status']
                    })
        
        return changes
