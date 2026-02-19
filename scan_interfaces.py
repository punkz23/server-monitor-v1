#!/usr/bin/env python
"""Script to re-scan and extract Sophos Firewall interfaces"""

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

def scan_interfaces():
    """Scan and extract interface information from Sophos firewall"""
    try:
        # Connect to firewall using the same method as our working scans
        client = SophosXGS126Client(
            host='192.168.253.2',
            port=4444,
            username='francois_ignacio',
            password='iCFIzzl1QjmwBV80@',
            verify_ssl=False
        )
        
        logger.info("Connecting to Sophos firewall...")
        
        # Try the same query that gave us interface statistics before
        # This is the query that worked in our DHCP scan
        interface_query = '''<Request>
    <Login>
        <Username>francois_ignacio</Username>
        <Password>iCFIzzl1QjmwBV80@</Password>
    </Login>
    <get>
        <InterfaceStatistics></InterfaceStatistics>
    </get>
</Request>'''
        
        logger.info("Querying interface statistics...")
        interface_response = client.session.post(
            'https://192.168.253.2:4444/webconsole/APIController',
            data=interface_query,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            verify=False
        )
        
        if interface_response.status_code == 200:
            response_text = interface_response.text
            logger.info(f"Response received, length: {len(response_text)}")
            
            # Check if we got XML or HTML
            if response_text.strip().startswith('<?xml'):
                logger.info("Received XML response - parsing interfaces...")
                
                try:
                    root = ET.fromstring(response_text)
                    
                    print("\n" + "="*60)
                    print("SOPHOS FIREWALL INTERFACES")
                    print("="*60)
                    
                    # Find all InterfaceStatistics entries
                    interfaces = root.findall('.//InterfaceStatistics')
                    
                    if interfaces:
                        print(f"\nFound {len(interfaces)} interfaces:")
                        print("-" * 40)
                        
                        for i, interface in enumerate(interfaces, 1):
                            name = interface.get('Name', f'Interface-{i}')
                            usage = interface.get('Usage', '0')
                            transaction_id = interface.get('transactionid', 'N/A')
                            
                            print(f"{i:2d}. {name:<20} Usage: {usage:<6} ID: {transaction_id}")
                    else:
                        print("No InterfaceStatistics entries found in XML")
                        
                        # Let's see what we did get
                        print("\nXML structure analysis:")
                        for child in root:
                            print(f"  - {child.tag}: {len(child)} children")
                            for subchild in child:
                                if hasattr(subchild, 'tag'):
                                    print(f"    - {subchild.tag}")
                                    if hasattr(subchild, 'attrib'):
                                        print(f"      Attributes: {subchild.attrib}")
                        
                except ET.ParseError as e:
                    logger.error(f"Error parsing XML: {e}")
                    print(f"Raw response (first 1000 chars):")
                    print(response_text[:1000])
                    
            else:
                logger.warning("Received HTML response instead of XML")
                print("Response appears to be HTML (login page)")
                print(f"First 500 chars: {response_text[:500]}")
                
        else:
            logger.error(f"HTTP Error: {interface_response.status_code}")
            print(f"Status code: {interface_response.status_code}")
            print(f"Response: {interface_response.text[:500]}")
                
    except Exception as e:
        logger.error(f"Error scanning interfaces: {e}")
        print(f"Exception: {e}")

if __name__ == "__main__":
    scan_interfaces()
