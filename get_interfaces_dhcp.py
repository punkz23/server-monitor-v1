#!/usr/bin/env python
"""Script to get interfaces using the same method as our working DHCP scan"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.sophos import SophosXGS126Client
import logging
import xml.etree.ElementTree as ET

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_interfaces_via_dhcp_method():
    """Get interfaces using the same successful method as DHCP scan"""
    try:
        # Connect to firewall
        client = SophosXGS126Client(
            host='192.168.253.2',
            port=4444,
            username='francois_ignacio',
            password='iCFIzzl1QjmwBV80@',
            verify_ssl=False
        )
        
        logger.info("Connecting to Sophos firewall...")
        
        # Use the exact same method that worked for DHCP leases
        # This returned interface statistics in our previous scan
        dhcp_response = client.get_dhcp_leases()
        
        if isinstance(dhcp_response, str) and dhcp_response.strip().startswith('<?xml'):
            logger.info("Got XML response - parsing for interfaces...")
            
            root = ET.fromstring(dhcp_response)
            
            print("\n" + "="*60)
            print("SOPHOS FIREWALL INTERFACES (from DHCP scan)")
            print("="*60)
            
            # Look for InterfaceStatistics entries
            interfaces = root.findall('.//InterfaceStatistics')
            
            if interfaces:
                print(f"\nFound {len(interfaces)} interfaces:")
                print("-" * 60)
                print(f"{'#':<3} {'Interface Name':<20} {'Usage':<10} {'Transaction ID':<15}")
                print("-" * 60)
                
                for i, interface in enumerate(interfaces, 1):
                    name_elem = interface.find('Name')
                    usage_elem = interface.find('Usage')
                    transaction_id = interface.get('transactionid', 'N/A')
                    
                    name = name_elem.text if name_elem is not None else f'Interface-{i}'
                    usage = usage_elem.text if usage_elem is not None else '0'
                    
                    print(f"{i:<3} {name:<20} {usage:<10} {transaction_id:<15}")
            else:
                print("No InterfaceStatistics entries found")
                
                # Show what we did find
                print("\nXML structure found:")
                for child in root:
                    print(f"  - {child.tag}")
                    for subchild in child:
                        print(f"    - {subchild.tag}: {subchild.attrib}")
                        
            print("\n" + "="*60)
            print("FULL XML RESPONSE (first 2000 chars):")
            print("="*60)
            print(dhcp_response[:2000])
            
        else:
            logger.warning(f"Unexpected response type: {type(dhcp_response)}")
            print(f"Response: {str(dhcp_response)[:500]}")
                
    except Exception as e:
        logger.error(f"Error getting interfaces: {e}")
        print(f"Exception: {e}")

if __name__ == "__main__":
    get_interfaces_via_dhcp_method()
