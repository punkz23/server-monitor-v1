#!/usr/bin/env python
"""Script to display Sophos Firewall interfaces"""

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
        
        # Try to get interface information
        # Method 1: Try to get interface statistics
        interfaces_response = client.session.get(
            'https://192.168.253.2:4444/webconsole/APIController',
            params={'reqxml': '<Request><InterfaceStatistics></InterfaceStatistics></Request>'},
            verify=False
        )
        
        if interfaces_response.status_code == 200:
            logger.info("Interface Statistics Response:")
            print(interfaces_response.text[:1000])
            
        # Method 2: Try general interface query
        interface_query = '''<Request>
    <Login>
        <Username>francois_ignacio</Username>
        <Password>iCFIzzl1QjmwBV80@</Password>
    </Login>
    <get>
        <Interface></Interface>
    </get>
</Request>'''
        
        interface_response = client.session.post(
            'https://192.168.253.2:4444/webconsole/APIController',
            data=interface_query,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            verify=False
        )
        
        if interface_response.status_code == 200:
            logger.info("Interface Query Response:")
            print(interface_response.text[:1000])
            
        # Method 3: Try to get system info
        system_query = '''<Request>
    <Login>
        <Username>francois_ignacio</Username>
        <Password>iCFIzzl1QjmwBV80@</Password>
    </Login>
    <get>
        <System></System>
    </get>
</Request>'''
        
        system_response = client.session.post(
            'https://192.168.253.2:4444/webconsole/APIController',
            data=system_query,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            verify=False
        )
        
        if system_response.status_code == 200:
            logger.info("System Info Response:")
            print(system_response.text[:1000])
            
    except Exception as e:
        logger.error(f"Error getting interfaces: {e}")

if __name__ == "__main__":
    get_firewall_interfaces()
