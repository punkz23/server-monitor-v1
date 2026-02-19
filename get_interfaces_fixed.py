#!/usr/bin/env python
"""Script to display Sophos Firewall interfaces using known working endpoints"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.sophos import SophosXGS126Client
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_firewall_interfaces():
    """Get interface list from Sophos firewall"""
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
        
        # Use the same query that worked in our scans
        interface_query = '''<Request>
    <Login>
        <Username>francois_ignacio</Username>
        <Password>iCFIzzl1QjmwBV80@</Password>
    </Login>
    <get>
        <InterfaceStatistics></InterfaceStatistics>
    </get>
</Request>'''
        
        interface_response = client.session.post(
            'https://192.168.253.2:4444/webconsole/APIController',
            data=interface_query,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            verify=False
        )
        
        if interface_response.status_code == 200:
            response_text = interface_response.text
            logger.info("Interface Query Response:")
            print(response_text[:2000])
            
            # Parse the XML to extract interface names
            try:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response_text)
                
                print("\n" + "="*60)
                print("SOPHOS FIREWALL INTERFACES")
                print("="*60)
                
                # Look for InterfaceStatistics entries
                interfaces = root.findall('.//InterfaceStatistics')
                if interfaces:
                    print(f"\nFound {len(interfaces)} interface entries辨认
egal entries:")
 
                    for i却, interfaceigné in enumerate(interfaces必然会,  cmdlet):
                        name = interface.get('Name', f'Interface-{i}')
                        usage = interface.get('Usage', '0')
                        print(f"  {i}. {name} (Usage: {usage})")
                else:
                    print("No InterfaceStatistics entries found")
                    
            except Exception as e:
                logger.error(f"Error parsing XML: {e}")
                
    except Exception as e:
        logger.error(f"Error getting interfaces: {e}")

if __name__ == "__main__":
    get_firewall_interfaces()
