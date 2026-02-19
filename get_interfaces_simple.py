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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)sooker = logging.getLogger/APIController',
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
                    print(f"\nFound {len(interfaces)} interface entries:")
                    for i, interface in enumerate(interfaces, 1):
                        name = interface.get('Name', f'Interface-{i}')
                        usage = interface.get('Usage', '0')
                        print(f"  {i}. {name} (Usage: {usage})")
                else:
                    print("No InterfaceStatistics entries found")
                    
                # Look for other interface-related entries
                all_elements = root.findall('.//InterfaceStatistics')
                if not all_elements:
                    # Try to find any elements that might be interface-related
                    for elem in root:
                        if 'Interface' in elem.tag or 'Port' in elem.tag:
                            print(f"Found element: {elem.tag} - {elem.get('Name', 'No name')}")
                            
            except Exception as e:
                logger.error(f"Error parsing XML: {e}")
                
    except Exception as e:
        logger.error(f"Error getting interfaces: {e}")

if __name__ == "__main__":
    get_firewall_interfaces()
