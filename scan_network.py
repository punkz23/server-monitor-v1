#!/usr/bin/env python
"""Script to scan devices on the 172.10.10.0/24 network"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.services.network_scanner import NetworkScanner
import json

def scan_local_networks():
    """Scan all local networks and display results"""
    print("Scanning local networks...")
    print("This may take a few minutes...\n")
    
    # Initialize scanner
    scanner = NetworkScanner(timeout=2, max_threads=30)
    
    # Get local networks
    networks = scanner.get_local_networks()
    
    # Add the specific network from your image
    networks.insert(0, "172.10.10.0/24")
    
    all_devices = []
    
    for network_range in networks:
        print(f"Scanning {network_range}...")
        try:
            devices = scanner.scan_network(network_range)
            all_devices.extend(devices)
            print(f"  Found {len(devices)} devices")
        except Exception as e:
            print(f"  Error scanning {network_range}: {e}")
    
    # Also try ARP table scanning
    print("\nScanning ARP table for additional devices...")
    arp_devices = scan_arp_table()
    all_devices.extend(arp_devices)
    print(f"Found {len(arp_devices)} devices from ARP table")
    
    # Remove duplicates based on IP address
    unique_devices = []
    seen_ips = set()
    for device in all_devices:
        if device['ip_address'] not in seen_ips:
            unique_devices.append(device)
            seen_ips.add(device['ip_address'])
    
    return unique_devices

def scan_arp_table():
    """Parse ARP table to get connected devices"""
    import subprocess
    import re
    
    devices = []
    try:
        result = subprocess.run(['arp', '-a'], capture_output=True, text=True, timeout=10)
        
        for line in result.stdout.split('\n'):
            # Parse ARP table entries
            # Format varies, but typically: "  192.168.1.1           00-11-22-33-44-55     dynamic"
            match = re.search(r'(\d+\.\d+\.\d+\.\d+)\s+([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', line)
            if match:
                ip = match.group(1)
                mac = match.group(0).split()[-1] if ' ' in match.group(0) else match.group(0)
                
                # Clean up MAC address format
                mac = mac.replace('-', ':').upper()
                
                device = {
                    'ip_address': ip,
                    'mac_address': mac,
                    'hostname': None,
                    'vendor': 'Unknown',
                    'device_type': 'unknown',
                    'open_ports': {}
                }
                
                # Try to get vendor from MAC
                scanner = NetworkScanner()
                mac_prefix = mac[:8]
                device['vendor'] = scanner.VENDOR_PREFIXES.get(mac_prefix, 'Unknown')
                
                devices.append(device)
                
    except Exception as e:
        print(f"Error scanning ARP table: {e}")
    
    return devices

def main():
    """Scan local networks and display results"""
    devices = scan_local_networks()
    
    # Display results
    print(f"Found {len(devices)} devices:\n")
    print("=" * 80)
    
    for i, device in enumerate(devices, 1):
        print(f"Device {i}:")
        print(f"  IP Address: {device['ip_address']}")
        print(f"  MAC Address: {device['mac_address'] or 'Unknown'}")
        print(f"  Hostname: {device['hostname']}")
        print(f"  Vendor: {device['vendor']}")
        print(f"  Device Type: {device['device_type']}")
        
        # Show open ports
        open_ports = [port for port, is_open in device['open_ports'].items() if is_open]
        if open_ports:
            print(f"  Open Ports: {', '.join(map(str, open_ports))}")
        else:
            print(f"  Open Ports: None detected")
        
        print("-" * 40)
    
    # Save results to JSON file
    with open('scan_results.json', 'w') as f:
        json.dump(devices, f, indent=2)
    
    print(f"\nResults saved to scan_results.json")
    print(f"Scan completed. Found {len(devices)} devices across all networks")

if __name__ == "__main__":
    main()
