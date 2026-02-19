#!/usr/bin/env python
"""Test script to verify firewall-based bandwidth measurement"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.isp_monitor import ISPMonitor
from monitor.models import ISPConnection
from monitor.services.firewall_interface_monitor import FirewallInterfaceMonitor

def test_firewall_bandwidth():
    print('=== Testing Firewall-Based Bandwidth Measurement ===')
    
    # Test PLDT
    try:
        pldt = ISPConnection.objects.filter(name__icontains='pldt').first()
        if pldt:
            print(f'Testing PLDT: {pldt.name} (Gateway: {pldt.gateway_ip})')
            monitor = ISPMonitor(pldt)
            bandwidth = monitor.test_bandwidth()
            print(f'PLDT Bandwidth result: {bandwidth} Mbps')
        else:
            print('No PLDT ISP connection found')
    except Exception as e:
        print(f'PLDT test error: {e}')
    
    # Test Converge
    try:
        converge = ISPConnection.objects.filter(name__icontains='converge').first()
        if converge:
            print(f'\nTesting Converge: {converge.name} (Gateway: {converge.gateway_ip})')
            monitor = ISPMonitor(converge)
            bandwidth = monitor.test_bandwidth()
            print(f'Converge Bandwidth result: {bandwidth} Mbps')
        else:
            print('No Converge ISP connection found')
    except Exception as e:
        print(f'Converge test error: {e}')
    
    # Check firewall interfaces
    try:
        print('\n=== Firewall Interface Data ===')
        firewall = FirewallInterfaceMonitor()
        interfaces = firewall.get_interfaces()
        
        wan_interfaces = []
        for interface in interfaces:
            name = interface.get('name', '').lower()
            if 'wan' in name or 'pldt' in name or 'converge' in name:
                wan_interfaces.append(interface)
        
        print(f'Found {len(wan_interfaces)} WAN-related interfaces:')
        for interface in wan_interfaces:
            name = interface.get('name', 'Unknown')
            usage = interface.get('usage', 0)
            ip = interface.get('ip_address', 'N/A')
            status = interface.get('status', 'Unknown')
            print(f'  - {name}: Usage={usage}, IP={ip}, Status={status}')
            
    except Exception as e:
        print(f'Firewall interface error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_firewall_bandwidth()
