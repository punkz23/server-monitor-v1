#!/usr/bin/env python
"""Sophos Firewall-based Network Scanner for Django"""

import os
import sys
import django
import json
import logging
from datetime import datetime
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
    """Scanner that uses Sophos Firewall API to discover network devices"""
    
    def __init__(self, firewall_host='192.168.253.2', firewall_port=4443, 
                 username='admin', password=None):
        """Initialize with firewall connection details"""
        self.firewall_host = firewall_host
        self.firewall_port = firewall_port
        self.username = username
        self.password = password
        self.client = None
        
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
    
    def _normalize_arp_entry(self, entry: Dict) -> Optional[Dict]:
        """Normalize ARP entry to device format"""
        try:
            if not entry.get('ip') or not entry.get('mac'):
                return None
                
            return {
                'ip_address': entry['ip'],
                'mac_address': entry['mac'],
                'hostname': entry.get('hostname', ''),
                'vendor': entry.get('vendor', 'Unknown'),
                'device_type': self._identify_device_type(entry),
                'source': 'arp'
            }
        except Exception as e:
            logger.error(f"Error normalizing ARP entry: {e}")
            return None
    
    def _normalize_dhcp_lease(self, lease: Dict) -> Optional[Dict]:
        """Normalize DHCP lease to device format"""
        try:
            if not lease.get('ip'):
                return None
                
            return {
                'ip_address': lease['ip'],
                'mac_address': lease.get('mac', ''),
                'hostname': lease.get('hostname', ''),
                'vendor': lease.get('vendor', 'Unknown'),
                'device_type': self._identify_device_type(lease),
                'source': 'dhcp'
            }
        except Exception as e:
            logger.error(f"Error normalizing DHCP lease: {e}")
            return None
    
    def _normalize_network_host(self, host: Dict) -> Optional[Dict]:
        """Normalize network host to device format"""
        try:
            if not host.get('ip'):
                return None
                
            return {
                'ip_address': host['ip'],
                'mac_address': host.get('mac', ''),
                'hostname': host.get('hostname', ''),
                'vendor': host.get('vendor', 'Unknown'),
                'device_type': self._identify_device_type(host),
                'source': 'hosts'
            }
        except Exception as e:
            logger.error(f"Error normalizing network host: {e}")
            return None
    
    def _identify_device_type(self, device_info: Dict) -> str:
        """Identify device type based on available information"""
        hostname = device_info.get('hostname', '').lower()
        mac = device_info.get('mac', '').upper()
        
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
        
        return NetworkDevice.TYPE_UNKNOWN
    
    def scan_all_devices(self) -> List[Dict]:
        """Scan all available sources and merge results"""
        if not self.connect():
            return []
        
        all_devices = []
        
        # Scan from different sources
        arp_devices = self.scan_arp_table()
        dhcp_devices = self.scan_dhcp_leases()
        host_devices = self.scan_network_hosts()
        
        # Merge devices, preferring ARP data
        device_map = {}
        
        # Add ARP devices first (most reliable)
        for device in arp_devices:
            key = device['ip_address']
            device_map[key] = device
        
        # Add DHCP devices
        for device in dhcp_devices:
            key = device['ip_address']
            if key not in device_map:
                device_map[key] = device
            else:
                # Merge hostname if missing
                if not device_map[key]['hostname'] and device['hostname']:
                    device_map[key]['hostname'] = device['hostname']
        
        # Add host devices
        for device in host_devices:
            key = device['ip_address']
            if key not in device_map:
                device_map[key] = device
        
        all_devices = list(device_map.values())
        logger.info(f"Total unique devices found: {len(all_devices)}")
        
        return all_devices
    
    def update_database(self, devices: List[Dict]) -> Dict:
        """Update database with discovered devices"""
        created_count = 0
        updated_count = 0
        
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
                    logger.info(f"Updated: {existing_device.name} ({existing_device.ip_address})")
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
                    logger.info(f"Created: {new_device.name} ({new_device.ip_address})")
                    
            except Exception as e:
                logger.error(f"Error processing device {device_info.get('ip_address', 'unknown')}: {e}")
        
        # Mark old devices as inactive
        recent_cutoff = timezone.now() - timezone.timedelta(hours=24)
        inactive_count = NetworkDevice.objects.filter(
            auto_discovered=True,
            last_seen__lt=recent_cutoff,
            is_active=True
        ).update(is_active=False)
        
        if inactive_count > 0:
            logger.info(f"Marked {inactive_count} devices as inactive")
        
        return {
            'created': created_count,
            'updated': updated_count,
            'inactive': inactive_count,
            'total': created_count + updated_count
        }

def main():
    """Main function to run Sophos network scan"""
    print("Sophos Firewall Network Scanner")
    print("=" * 40)
    
    # Get firewall password
    password = input("Enter Sophos firewall password: ").strip()
    
    scanner = SophosNetworkScanner(password=password)
    
    print("\nScanning network devices via Sophos firewall...")
    devices = scanner.scan_all_devices()
    
    if devices:
        print(f"\nFound {len(devices)} devices:")
        for device in devices[:10]:  # Show first 10
            print(f"  {device['ip_address']:15} {device['hostname']:20} {device['device_type']}")
        
        if len(devices) > 10:
            print(f"  ... and {len(devices) - 10} more devices")
        
        response = input("\nUpdate database with these devices? (y/N): ")
        if response.lower() in ['y', 'yes']:
            results = scanner.update_database(devices)
            print(f"\nDatabase updated:")
            print(f"  Created: {results['created']} devices")
            print(f"  Updated: {results['updated']} devices")
            print(f"  Marked inactive: {results['inactive']} devices")
        else:
            print("Database update cancelled.")
    else:
        print("No devices found.")

if __name__ == "__main__":
    main()
