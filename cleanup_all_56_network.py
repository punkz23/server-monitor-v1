#!/usr/bin/env python
"""Clean up all unreachable devices from 192.168.56.0/24 network"""

import os
import sys
import django
import subprocess
import concurrent.futures
from datetime import datetime

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

def cleanup_all_unreachable_devices():
    """Remove all unreachable devices from 192.168.56.0/24 network"""
    devices = NetworkDevice.objects.filter(network='192.168.56.0/24').order_by('ip_address')
    
    print(f"Checking all {devices.count()} devices in 192.168.56.0/24 network...")
    print("=" * 80)
    
    devices_to_delete = []
    devices_to_keep = []
    
    # Check each device
    for device in devices:
        is_reachable = ping_device(device.ip_address)
        
        if is_reachable:
            devices_to_keep.append(device)
            print(f"KEEP: {device.ip_address:15} {device.name:20} (REACHABLE)")
        else:
            devices_to_delete.append(device)
            print(f"DELETE: {device.ip_address:15} {device.name:20} (UNREACHABLE)")
    
    print("-" * 80)
    print(f"Summary: {len(devices_to_keep)} reachable, {len(devices_to_delete)} unreachable")
    
    if devices_to_delete:
        print(f"\nDeleting {len(devices_to_delete)} unreachable devices...")
        
        # Delete unreachable devices
        deleted_count = 0
        for device in devices_to_delete:
            device_name = device.name
            device_ip = device.ip_address
            device.delete()
            deleted_count += 1
            if deleted_count <= 10:  # Show first 10 deletions
                print(f"Deleted: {device_name} ({device_ip})")
            elif deleted_count == 11:
                print(f"... and {len(devices_to_delete) - 10} more devices")
        
        print(f"Successfully deleted {deleted_count} devices")
    else:
        print("No devices to delete")
    
    # Show remaining devices
    remaining_devices = NetworkDevice.objects.filter(network='192.168.56.0/24').count()
    print(f"\nRemaining devices in 192.168.56.0/24: {remaining_devices}")
    
    print(f"Cleanup completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return len(devices_to_delete)

if __name__ == "__main__":
    print("Complete Network Device Cleanup Script")
    print("=" * 40)
    print("This script will remove ALL unreachable devices from the 192.168.56.0/24 network")
    print("Only your PC (192.168.56.1) should remain after cleanup")
    print()
    
    response = input("Do you want to continue? (y/N): ")
    if response.lower() in ['y', 'yes']:
        deleted_count = cleanup_all_unreachable_devices()
        print(f"\nCleanup completed. Deleted {deleted_count} unreachable devices.")
    else:
        print("Cleanup cancelled.")
