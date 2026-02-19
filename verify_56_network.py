#!/usr/bin/env python
"""Verify if devices in 192.168.56.0/24 network actually exist by pinging them"""

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
        # Windows ping command
        result = subprocess.run(
            ['ping', '-n', '1', '-w', str(timeout * 1000), ip_address],
            capture_output=True,
            text=True,
            timeout=timeout + 1
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        return False

def verify_devices():
    """Verify all devices in 192.168.56.0/24 network"""
    devices = NetworkDevice.objects.filter(network='192.168.56.0/24').order_by('ip_address')
    
    print(f"Verifying {devices.count()} devices in 192.168.56.0/24 network...")
    print("=" * 80)
    print(f"{'IP Address':15} {'Device Name':20} {'Status':8} {'Response Time':12}")
    print("-" * 80)
    
    reachable_count = 0
    unreachable_count = 0
    
    # Ping devices in parallel for faster results
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_device = {
            executor.submit(ping_device, device.ip_address): device 
            for device in devices
        }
        
        for future in concurrent.futures.as_completed(future_to_device):
            device = future_to_device[future]
            is_reachable = future.result()
            
            if is_reachable:
                status = "REACHABLE"
                reachable_count += 1
            else:
                status = "UNREACHABLE"
                unreachable_count += 1
            
            print(f"{device.ip_address:15} {device.name:20} {status:8} {'N/A':12}")
    
    print("-" * 80)
    print(f"Summary: {reachable_count} reachable, {unreachable_count} unreachable")
    print(f"Verification completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return reachable_count, unreachable_count

if __name__ == "__main__":
    verify_devices()
