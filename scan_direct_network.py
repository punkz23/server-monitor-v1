#!/usr/bin/env python3
"""
Direct Network Scanner for 172.10.10.0/24
Uses ping, ARP table scanning, and port scanning to discover devices
"""

import sys
import os
import json
import logging
import subprocess
import socket
import threading
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
import django
django.setup()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DirectNetworkScanner:
    """Direct network scanner using ping and port scanning"""
    
    def __init__(self, network="172.10.10.0/24"):
        self.network = network
        self.base_ip = "172.10.10"
        self.devices = []
        self.lock = threading.Lock()
    
    def ping_host(self, ip):
        """Ping a single host to check if it's alive"""
        try:
            # Windows ping command
            cmd = ['ping', '-n', '1', '-w', '1000', ip]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
            
            if result.returncode == 0:
                # Extract round-trip time
                output = result.stdout
                if "TTL=" in output:
                    # Parse ping response for additional info
                    device_info = {
                        'ip': ip,
                        'status': 'alive',
                        'pingable': True,
                        'response_time': self._extract_ping_time(output),
                        'ttl': self._extract_ttl(output)
                    }
                    return device_info
            return None
            
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, Exception):
            return None
    
    def _extract_ping_time(self, ping_output):
        """Extract round-trip time from ping output"""
        try:
            import re
            # Look for time in milliseconds
            match = re.search(r'time[=<](\d+)ms', ping_output)
            if match:
                return int(match.group(1))
            return None
        except:
            return None
    
    def _extract_ttl(self, ping_output):
        """Extract TTL from ping output"""
        try:
            import re
            match = re.search(r'TTL=(\d+)', ping_output)
            if match:
                return int(match.group(1))
            return None
        except:
            return None
    
    def scan_port(self, ip, port, timeout=1):
        """Scan a single port on a host"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def get_arp_table(self):
        """Get ARP table entries for the network"""
        try:
            # Windows ARP command
            cmd = ['arp', '-a']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            arp_entries = []
            for line in result.stdout.split('\n'):
                if self.base_ip in line:
                    # Parse ARP entry
                    parts = line.split()
                    if len(parts) >= 2:
                        ip = parts[1]
                        mac = parts[0] if ':' in parts[0] else parts[2] if ':' in parts[2] else None
                        
                        if ip.startswith(self.base_ip) and mac:
                            arp_entries.append({
                                'ip': ip,
                                'mac': mac,
                                'type': 'arp_entry'
                            })
            
            return arp_entries
            
        except Exception as e:
            logger.error(f"Failed to get ARP table: {e}")
            return []
    
    def scan_host_ports(self, ip, common_ports=None):
        """Scan common ports on a host"""
        if common_ports is None:
            common_ports = [22, 23, 53, 80, 135, 139, 443, 445, 993, 995, 1723, 3389, 5900]
        
        open_ports = []
        
        for port in common_ports:
            if self.scan_port(ip, port, timeout=0.5):
                open_ports.append(port)
        
        return open_ports
    
    def scan_network(self):
        """Main scanning function"""
        logger.info(f"Starting direct network scan for {self.network}")
        logger.info("This will use ping, ARP table, and port scanning methods")
        
        # Step 1: Get ARP table entries
        logger.info("Step 1: Checking ARP table for network devices...")
        arp_devices = self.get_arp_table()
        logger.info(f"Found {len(arp_devices)} ARP entries for {self.base_ip}.*")
        
        # Step 2: Ping scan all IPs in the range
        logger.info("Step 2: Pinging all IPs in 172.10.10.1-254...")
        ping_devices = []
        
        # Use thread pool for faster ping scanning
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            for i in range(1, 255):
                ip = f"{self.base_ip}.{i}"
                future = executor.submit(self.ping_host, ip)
                futures.append(future)
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    ping_devices.append(result)
                    logger.info(f"Host alive: {result['ip']} (TTL: {result.get('ttl')}, Time: {result.get('response_time')}ms)")
        
        logger.info(f"Ping scan completed. Found {len(ping_devices)} responsive hosts")
        
        # Step 3: Port scan responsive hosts
        logger.info("Step 3: Port scanning responsive hosts...")
        for device in ping_devices:
            ip = device['ip']
            logger.info(f"Scanning ports on {ip}...")
            open_ports = self.scan_host_ports(ip)
            device['open_ports'] = open_ports
            device['port_count'] = len(open_ports)
            
            if open_ports:
                logger.info(f"  Open ports on {ip}: {', '.join(map(str, open_ports))}")
        
        # Step 4: Merge ARP and ping data
        logger.info("Step 4: Merging scan results...")
        all_devices = []
        
        # Add ping devices
        for ping_device in ping_devices:
            # Look for matching ARP entry
            matching_arp = None
            for arp_device in arp_devices:
                if arp_device['ip'] == ping_device['ip']:
                    matching_arp = arp_device
                    break
            
            # Merge device information
            merged_device = ping_device.copy()
            if matching_arp:
                merged_device['mac'] = matching_arp['mac']
                merged_device['arp_entry'] = True
            else:
                merged_device['arp_entry'] = False
            
            all_devices.append(merged_device)
        
        # Add ARP-only devices (didn't respond to ping but in ARP table)
        for arp_device in arp_devices:
            if not any(d['ip'] == arp_device['ip'] for d in all_devices):
                arp_device.update({
                    'status': 'arp_only',
                    'pingable': False,
                    'open_ports': [],
                    'port_count': 0
                })
                all_devices.append(arp_device)
        
        # Sort devices by IP
        all_devices.sort(key=lambda x: x['ip'])
        
        # Step 5: Identify device types based on open ports
        for device in all_devices:
            device['device_type'] = self._identify_device_type(device)
        
        self.devices = all_devices
        
        # Save results
        results = {
            'scan_time': datetime.now().isoformat(),
            'target_network': self.network,
            'scan_method': 'direct_ping_arp_port',
            'total_devices_found': len(all_devices),
            'ping_responsive': len([d for d in all_devices if d.get('pingable')]),
            'arp_entries': len([d for d in all_devices if d.get('arp_entry')]),
            'devices': all_devices
        }
        
        output_file = 'direct_scan_results.json'
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved to {output_file}")
        return results
    
    def _identify_device_type(self, device):
        """Identify device type based on open ports and other characteristics"""
        open_ports = device.get('open_ports', [])
        
        # Common device type signatures
        if 80 in open_ports or 443 in open_ports:
            if 22 in open_ports:
                return 'Linux Server (SSH+Web)'
            elif 3389 in open_ports:
                return 'Windows Server (RDP+Web)'
            else:
                return 'Web Server/Router'
        
        if 22 in open_ports:
            return 'Linux/Unix Device (SSH)'
        
        if 3389 in open_ports:
            return 'Windows Machine (RDP)'
        
        if 135 in open_ports and 445 in open_ports:
            return 'Windows File Share'
        
        if 53 in open_ports:
            return 'DNS Server'
        
        if device.get('arp_entry') and not device.get('pingable'):
            return 'Network Device (ARP only)'
        
        if device.get('pingable'):
            return 'Active Host'
        
        return 'Unknown'
    
    def display_results(self, results):
        """Display scan results"""
        print(f"\nDirect Network Scan Results")
        print(f"==========================")
        print(f"Target Network: {self.network}")
        print(f"Scan Method: Direct Ping + ARP + Port Scan")
        print(f"Total Devices Found: {results['total_devices_found']}")
        print(f"Ping Responsive: {results['ping_responsive']}")
        print(f"ARP Entries: {results['arp_entries']}")
        print(f"")
        
        for device in results['devices']:
            print(f"Device: {device['ip']}")
            print(f"  MAC: {device.get('mac', 'N/A')}")
            print(f"  Status: {device.get('status', 'N/A')}")
            print(f"  Type: {device.get('device_type', 'N/A')}")
            print(f"  Pingable: {'Yes' if device.get('pingable') else 'No'}")
            print(f"  Response Time: {device.get('response_time', 'N/A')}ms")
            print(f"  TTL: {device.get('ttl', 'N/A')}")
            
            if device.get('open_ports'):
                print(f"  Open Ports: {', '.join(map(str, device['open_ports']))}")
            else:
                print(f"  Open Ports: None detected")
            
            print(f"")

def main():
    """Main function"""
    scanner = DirectNetworkScanner()
    results = scanner.scan_network()
    scanner.display_results(results)
    
    print(f"\nScan completed. Found {results['total_devices_found']} devices on 172.10.10.0/24")

if __name__ == "__main__":
    main()
