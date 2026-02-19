#!/usr/bin/env python
"""Script to check network distribution"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.models import NetworkDevice
from django.db.models import Count

# Show network distribution
networks = NetworkDevice.objects.values('network').annotate(count=Count('id')).order_by('network')
print('Current network distribution:')
for network in networks:
    print(f'  {network["network"]}: {network["count"]} devices')

print(f'\nTotal devices: {NetworkDevice.objects.count()}')
