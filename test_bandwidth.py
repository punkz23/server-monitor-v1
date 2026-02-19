#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.models import NetworkDevice, DeviceBandwidthUsage
from monitor.services.sophos_service import SophosMonitoringService
from django.utils import timezone

# Get the firewall device
firewall = NetworkDevice.objects.filter(device_type=NetworkDevice.TYPE_FIREWALL).first()
if firewall:
    print(f'Testing firewall: {firewall.name} ({firewall.ip_address})')
    print(f'API Port: {firewall.api_port}')
    print(f'API Username: {firewall.api_username or "Not set"}')
    print(f'API Token: {"Set" if firewall.api_token else "Not set"}')
    
    # Try to initialize the service
    try:
        service = SophosMonitoringService(firewall)
        if service.client:
            print('Service initialized successfully')
            
            # Try to get some data
            try:
                events = service.client.get_security_events(limit=5)
                print(f'Security events type: {type(events)}')
                if isinstance(events, str):
                    print(f'Events preview: {events[:200]}...')
                elif isinstance(events, list):
                    print(f'Events list length: {len(events)}')
                    if events:
                        print(f'First event: {events[0]}')
                else:
                    print(f'Events: {events}')
            except Exception as e:
                print(f'Error getting security events: {e}')
        else:
            print('Failed to initialize service client')
    except Exception as e:
        print(f'Error initializing service: {e}')
else:
    print('No firewall device found')
