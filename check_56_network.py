#!/usr/bin/env python
"""Check source of devices in 192.168.56.0/24 network"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.models import NetworkDevice

# Get devices from 192.168.56.0/24 network
devices = NetworkDevice.objects.filter(network='192.168.56.0/24').order_by('first_seen')

print('Devices in 192.168.56.0/24 network:')
print('=' * 80)
print(f'{"Device Name":20} {"IP Address":15} {"Type":12} {"Auto Disc":8} {"First Seen":16} {"Last Seen":16}')
print('-' * 80)

for device in devices:
    print(f'{device.name:20} {device.ip_address:15} {device.get_device_type_display():12} {str(device.auto_discovered):8} {device.first_seen.strftime("%Y-%m-%d %H:%M"):16} {device.last_seen.strftime("%Y-%m-%d %H:%M"):16}')

print(f'\nTotal devices: {devices.count()}')

# Check discovery methods
auto_discovered = devices.filter(auto_discovered=True).count()
manual_added = devices.filter(auto_discovered=False).count()
print(f'Auto-discovered: {auto_discovered}')
print(f'Manually added: {manual_added}')

# Check when they were first discovered
first_seen_dates = devices.values_list('first_seen', flat=True).distinct()
print(f'First discovery dates: {sorted(set(first_seen_dates))}')
