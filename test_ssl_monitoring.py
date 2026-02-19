#!/usr/bin/env python
"""Test SSL certificate monitoring"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.models import NetworkDevice
from monitor.views import get_ssl_certificates_for_device

def test_ssl_monitoring():
    print('=== Testing SSL Certificate Monitoring ===')
    
    # Find SSL-capable devices
    devices = NetworkDevice.objects.filter(device_type__in=['WEB_SERVER', 'FIREWALL', 'ROUTER'], enabled=True)
    print(f'Found {devices.count()} SSL-capable devices:')
    
    for device in devices:
        print(f'\nTesting {device.name} ({device.device_type}) - {device.ip_address}')
        
        try:
            ssl_certs = get_ssl_certificates_for_device(device)
            print(f'SSL certificates found: {len(ssl_certs)}')
            
            for port, cert in ssl_certs.items():
                status = cert.get('status', 'unknown')
                days = cert.get('days_remaining', 'unknown')
                subject = cert.get('subject_common_name', 'unknown')
                print(f'  Port {port}: {status} - {days} days - {subject}')
                
        except Exception as e:
            print(f'Error: {e}')
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_ssl_monitoring()
