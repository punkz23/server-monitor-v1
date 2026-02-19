#!/usr/bin/env python
"""Verify devices in problematic networks"""

import os
import sys
import django
import subprocess
import concurrent.futures

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.models import NetworkDevice

def ping_device(ip_address, timeout=2):
    """Ping a device to check if it's reachable"""
    try:
        result = subprocess.run(
            ['ping', '-n', '1', '-w', str(timeout * 1000), ip_address],
            capture_output=True,
            text=True,
            timeout=timeout + 1
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        return False

def check_network_reachability(network_name):
    """Check reachability of devices in a network"""
    devices = NetworkDevice.objects.filter(network=network_name).order_by('ip_address')
    
    print(f"\nChecking {devices.count()} devices in {network_name}:")
    print("=" * 60)
    
    reachable = 0
    unreachable = 0
    
    # Check first 20 devices as sample
    sample_devices = devices[:20]
    
    for device in sample_devices:
        is_reachable = ping_device(device.ip_address)
        if is_reachable:
            reachable += 1
            print(f"REACHABLE: {device.ip_address:15} {device.name:20}")
        else:
            unreachable += 1
            print(f"UNREACHABLE: {device.ip_address:15} {device.name:20}")
    
    if devices.count() > 20:
        print(f"... and {devices.count() - 20} more devices")
    
    print(f"\nSample results: {reachable} reachable, {unreachable} unreachable")
    return reachable, unreachable

# Check problematic networks
print("Network Device Reachability Check")
print("=" * 40)

networks_to_check = ['192.168.56.0/24', '192.168.253.0/24']
total_reachable = 0
total_unreachable = 0

for network in networks_to_check:
    reachable, unreachable = check_network_reachability(network)
    total_reachable += reachable
    total_unreachable += unreachable

print(f"\nOverall sample: {total_reachable} reachable, {total_unreachable} unreachable")
