#!/usr/bin/env python
"""Check device count by network"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.models import NetworkDevice
from django.db.models import Count

# Get total device count
total = NetworkDevice.objects.count()
print(f'Total devices in database: {total}')
print()

# Group by network
print('Devices by network:')
networks = NetworkDevice.objects.values('network').annotate(count=Count('id')).order_by('-count')
for net in networks:
    network_name = net['network'] or 'Unknown'
    count = net['count']
    print(f'{network_name:20} {count:5} devices')

print()
print('Top 10 networks with most devices:')
for net in networks[:10]:
    network_name = net['network'] or 'Unknown'
    count = net['count']
    print(f'{network_name:20} {count:5} devices')
