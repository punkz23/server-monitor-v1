#!/usr/bin/env python
"""Optimized monitoring view with caching and performance improvements"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.models import Server, NetworkDevice, AlertEvent, SecurityEvent, NetworkMetric
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import time

def test_optimized_monitoring():
    print('🔍 Testing Optimized Monitoring Performance')
    print('=' * 60)
    
    # Test current monitoring performance
    start_time = time.time()
    
    # Get data (simulating current monitoring view)
    servers = Server.objects.all().order_by("-pinned", "name")
    network_devices = NetworkDevice.objects.filter(enabled=True).order_by("name")
    
    # Test SSL certificate checking performance
    ssl_devices = network_devices.filter(device_type__in=['WEB_SERVER', 'ROUTER'])
    print(f'📊 SSL Devices to check: {ssl_devices.count()}')
    
    ssl_start = time.time()
    for device in ssl_devices:
        device_start = time.time()
        
        # Simulate current SSL checking logic
        if device.ip_address in ['192.168.254.13', '192.168.254.50', '192.168.253.15']:
            print(f'🔍 Checking SSL for {device.name} ({device.ip_address})...')
            # This is the slow part - SSH connections
            # We'll simulate the time it takes
            time.sleep(0.5)  # Simulate SSH connection time
            device_time = time.time() - device_start
            print(f'   ⏱️  Took {device_time:.2f}s')
        else:
            device_time = time.time() - device_start
            print(f'🔍 Checking SSL for {device.name} ({device.ip_address})... {device_time:.2f}s')
    
    ssl_time = time.time() - ssl_start
    total_time = time.time() - start_time
    
    print(f'\\n📊 Performance Results:')
    print(f'⏱️  SSL Checking Time: {ssl_time:.2f}s')
    print(f'⏱️  Total Page Load Time: {total_time:.2f}s')
    
    # Test caching solution
    print(f'\\n💡 Proposed Solution: Caching')
    print(f'   🚀 Cache SSL certificates for 5 minutes')
    print(f'   🚀 Reduce page load from {ssl_time:.2f}s to ~0.1s')
    print(f'   🚀 Update cache via background task')
    
    # Test server status for 192.168.253.15
    print(f'\\n🔍 Testing 192.168.253.15 Status:')
    from monitor.services.server_status_monitor import ServerStatusMonitor
    monitor = ServerStatusMonitor()
    
    is_up = monitor.check_server_status('192.168.253.15')
    print(f'📊 Current monitoring result: {"UP" if is_up else "DOWN"}')
    
    if is_up:
        print('❌ ISSUE: Still showing as UP due to ping false positive')
    else:
        print('✅ FIXED: Now correctly showing as DOWN')

if __name__ == '__main__':
    test_optimized_monitoring()
