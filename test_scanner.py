#!/usr/bin/env python
"""Test network scanner initialization"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.services.network_scanner import NetworkScanner

# Test scanner initialization
scanner = NetworkScanner()
print('Sophos scanner available:', hasattr(scanner, 'sophos_scanner') and scanner.sophos_scanner is not None)

# Test scan of 192.168.254.0/24
devices = scanner.scan_network('192.168.254.0/24')
print(f'Devices found: {len(devices)}')
if devices:
    print('First few devices:')
    for i, d in enumerate(devices[:3]):
        print(f'  {d["ip_address"]} - {d.get("hostname", "Unknown")}')
