#!/usr/bin/env python
"""Test script to verify Sophos firewall API connection"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.sophos import SophosXGS126Client
from monitor.sophos_xml_parser import SophosXMLParser
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_connection():
    """Test connection to Sophos firewall"""
    # Configuration - update these with your actual firewall details
    FIREWALL_HOST = "192.168.253.2"  # The actual firewall IP address
    FIREWALL_PORT = 4443  # Default Sophos API port
    USERNAME = "francois_ignacio"  # Update with actual username
    PASSWORD = "iCFIzzl1QjmwBV80@"  # Update with actual password
    
    print("Testing Sophos Firewall API Connection")
    print("=" * 50)
    print(f"Firewall: {FIREWALL_HOST}:{FIREWALL_PORT}")
    print(f"Username: {USERNAME}")
    print()
    
    try:
        # Create client
        print("Initializing client...")
        client = SophosXGS126Client(
            host=FIREWALL_HOST,
            port=FIREWALL_PORT,
            username=USERNAME,
            password=PASSWORD,
            verify_ssl=False
        )
        
        print("✓ Client initialized successfully")
        
        # Test basic API call
        print("\nTesting system status API call...")
        try:
            system_status = client.get_system_status()
            if system_status:
                print("✓ System status API call successful")
                if isinstance(system_status, str) and system_status.startswith('<?xml'):
                    print("✓ Response is XML format")
                    parsed = SophosXMLParser.parse_system_status(system_status)
                    print(f"✓ Parsed system data: {len(parsed)} fields")
                    for key, value in parsed.items():
                        print(f"  {key}: {value}")
                else:
                    print(f"Response type: {type(system_status)}")
                    print(f"Response content: {str(system_status)[:200]}...")
            else:
                print("✗ System status API call failed - empty response")
        except Exception as e:
            print(f"✗ System status API call failed: {e}")
        
        # Test interfaces API call
        print("\nTesting interfaces API call...")
        try:
            interfaces = client.get_interfaces()
            if interfaces:
                print("✓ Interfaces API call successful")
                if isinstance(interfaces, str) and interfaces.startswith('<?xml'):
                    print("✓ Response is XML format")
                    parsed = SophosXMLParser.parse_interfaces(interfaces)
                    print(f"✓ Parsed {len(parsed)} interfaces")
                    for iface in parsed[:3]:  # Show first 3
                        print(f"  Interface: {iface.get('name', 'unknown')}")
                else:
                    print(f"Response type: {type(interfaces)}")
                    print(f"Response content: {str(interfaces)[:200]}...")
            else:
                print("✗ Interfaces API call failed - empty response")
        except Exception as e:
            print(f"✗ Interfaces API call failed: {e}")
        
        # Test ARP table API call
        print("\nTesting ARP table API call...")
        try:
            arp_table = client.get_arp_table()
            if arp_table:
                print("✓ ARP table API call successful")
                if isinstance(arp_table, str) and arp_table.startswith('<?xml'):
                    print("✓ Response is XML format")
                    parsed = SophosXMLParser.parse_arp_table(arp_table)
                    print(f"✓ Parsed {len(parsed)} ARP entries")
                    for entry in parsed[:3]:  # Show first 3
                        ip = entry.get('ipaddress', entry.get('ip', 'unknown'))
                        mac = entry.get('macaddress', entry.get('mac', 'unknown'))
                        print(f"  {ip} -> {mac}")
                else:
                    print(f"Response type: {type(arp_table)}")
                    print(f"Response content: {str(arp_table)[:200]}...")
            else:
                print("✗ ARP table API call failed - empty response")
        except Exception as e:
            print(f"✗ ARP table API call failed: {e}")
        
        # Test DHCP leases API call
        print("\nTesting DHCP leases API call...")
        try:
            dhcp_leases = client.get_dhcp_leases()
            if dhcp_leases:
                print("✓ DHCP leases API call successful")
                if isinstance(dhcp_leases, str) and dhcp_leases.startswith('<?xml'):
                    print("✓ Response is XML format")
                    parsed = SophosXMLParser.parse_dhcp_leases(dhcp_leases)
                    print(f"✓ Parsed {len(parsed)} DHCP leases")
                    for lease in parsed[:3]:  # Show first 3
                        ip = lease.get('ipaddress', lease.get('ip', 'unknown'))
                        hostname = lease.get('hostname', lease.get('clientname', 'unknown'))
                        print(f"  {ip} -> {hostname}")
                else:
                    print(f"Response type: {type(dhcp_leases)}")
                    print(f"Response content: {str(dhcp_leases)[:200]}...")
            else:
                print("✗ DHCP leases API call failed - empty response")
        except Exception as e:
            print(f"✗ DHCP leases API call failed: {e}")
        
        print("\n" + "=" * 50)
        print("Connection test completed!")
        print("\nTo run the full network scan, update the credentials in scan_sophos_network.py")
        print("and run: python scan_sophos_network.py")
        
    except Exception as e:
        print(f"✗ Failed to initialize client: {e}")
        print("\nPossible issues:")
        print("1. Firewall IP address is incorrect")
        print("2. Firewall port is not 4443 (try 8443 or 443)")
        print("3. Username/password are incorrect")
        print("4. Firewall API is not enabled")
        print("5. Network connectivity issues")

if __name__ == "__main__":
    test_connection()
