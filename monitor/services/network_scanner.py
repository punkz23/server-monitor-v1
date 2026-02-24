import socket
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from ipaddress import IPv4Network, ip_address
import json
import re
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Import at the end to avoid circular imports
def get_network_device_model():
    """Get NetworkDevice model to avoid circular imports"""
    from monitor.models import NetworkDevice
    return NetworkDevice

# Try to import Sophos scanner
try:
    from sophos_scanner_service import SophosNetworkScanner
    SOPHOS_AVAILABLE = True
except ImportError:
    SOPHOS_AVAILABLE = False
    logger.warning("Sophos scanner not available, falling back to ping scanning")

class NetworkScanner:
    """Network device scanner that discovers devices on the network"""
    
    # Common ports to scan for device identification
    COMMON_PORTS = [21, 22, 23, 53, 80, 135, 139, 443, 445, 515, 631, 993, 995, 1723, 3389, 5000, 5001, 5900, 8080, 9100]
    
    # MAC address vendor prefixes for device identification
    VENDOR_PREFIXES = {
        # Mobile phone vendors
        '00:1A:2B': 'Apple',
        '28:CF:E9': 'Apple',
        'A4:C1:38': 'Apple',
        '40:A6:D9': 'Apple',
        '98:01:A7': 'Apple',
        '64:20:9F': 'Apple',
        'F0:18:98': 'Samsung',
        'E8:50:8B': 'Samsung',
        'AC:5D:9E': 'Samsung',
        '38:8F:71': 'Samsung',
        '28:E3:1F': 'Samsung',
        '00:12:1C': 'Huawei',
        '00:E0:FC': 'Huawei',
        'AC:C1:EE': 'Huawei',
        '70:72:3C': 'Huawei',
        '00:1D:E8': 'Xiaomi',
        '34:CE:00': 'Xiaomi',
        '64:09:80': 'Xiaomi',
        '78:11:DC': 'Xiaomi',
        
        # PC manufacturers
        '00:50:56': 'VMware',
        '08:00:27': 'VirtualBox',
        '00:0C:29': 'VMware',
        '00:1C:42': 'Parallels',
        '00:03:FF': 'Microsoft Hyper-V',
        'B8:27:EB': 'Raspberry Pi',
        'DC:A6:32': 'Raspberry Pi',
        'E4:5F:01': 'Raspberry Pi',
        '00:15:5D': 'Microsoft',
        'D0:67:E5': 'Dell',
        'F8:CA:B8': 'Dell',
        
        # Printer manufacturers
        '00:1E:4F': 'HP',
        '1C:CB:09': 'HP',
        '3C:D9:2B': 'HP',
        'C8:CB:B8': 'HP',
        '30:05:5C': 'HP',
        '00:10:83': 'Lexmark',
        '00:04:75': 'Lexmark',
        'C0:CB:38': 'Brother',
        '00:80:77': 'Brother',
        '08:39:35': 'Brother',
        '00:1A:6B': 'Canon',
        '00:1E:8F': 'Canon',
        'C4:2F:90': 'Canon',
        
        # Network equipment
        '00:04:23': 'Cisco',
        '00:0B:46': 'Cisco',
        '00:1D:A1': 'Cisco',
        '00:0C:42': 'MikroTik',
        'D4:CA:6D': 'MikroTik',
        '18:E8:29': 'TP-Link',
        '00:31:92': 'TP-Link',
        'B0:BE:76': 'TP-Link',
        'FC:EC:DA': 'Ubiquiti',
        '04:18:D6': 'Ubiquiti',
        '78:8A:20': 'Ubiquiti',
        '00:11:32': 'Synology',
        '00:08:9B': 'QNAP',
        'E0:D9:E3': 'D-Link',
        '00:04:23': 'Cisco',
        '00:0B:46': 'Cisco',
        '00:1D:A1': 'Cisco',
        '00:23:04': 'Cisco',
        '00:26:CB': 'Cisco',
        '00:1B:1F': 'Cisco',
        '00:17:94': 'Cisco',
        '00:1C:F0': 'Cisco',
        '00:21:A7': 'Cisco',
        '00:22:90': 'Cisco',
        '00:24:94': 'Cisco',
        '00:25:B3': 'Cisco',
        '00:26:64': 'Cisco',
        '00:27:0E': 'Cisco',
        '00:30:AB': 'Cisco',
        '00:90:0B': 'Cisco',
        '00:A0:C9': 'Cisco',
        '00:D0:02': 'Cisco',
        '00:D0:03': 'Cisco',
        '00:D0:04': 'Cisco',
        '00:D0:05': 'Cisco',
        '00:D0:06': 'Cisco',
        '00:D0:07': 'Cisco',
        '00:D0:08': 'Cisco',
        '00:D0:09': 'Cisco',
        '00:D0:3A': 'Cisco',
        '00:D0:3B': 'Cisco',
        '00:D0:3C': 'Cisco',
        '00:D0:3D': 'Cisco',
        '00:D0:3E': 'Cisco',
        '00:D0:3F': 'Cisco',
        '00:D0:40': 'Cisco',
        '00:D0:41': 'Cisco',
        '00:D0:42': 'Cisco',
        '00:D0:43': 'Cisco',
        '00:D0:44': 'Cisco',
        '00:D0:45': 'Cisco',
        '00:D0:46': 'Cisco',
        '00:D0:47': 'Cisco',
        '00:D0:48': 'Cisco',
        '00:D0:49': 'Cisco',
        '00:D0:4A': 'Cisco',
        '00:D0:4B': 'Cisco',
        '00:D0:4C': 'Cisco',
        '00:D0:4D': 'Cisco',
        '00:D0:4E': 'Cisco',
        '00:D0:4F': 'Cisco',
        '00:D0:50': 'Cisco',
        '00:D0:51': 'Cisco',
        '00:D0:52': 'Cisco',
        '00:D0:53': 'Cisco',
        '00:D0:54': 'Cisco',
        '00:D0:55': 'Cisco',
        '00:D0:56': 'Cisco',
        '00:D0:57': 'Cisco',
        '00:D0:58': 'Cisco',
        '00:D0:59': 'Cisco',
        '00:D0:5A': 'Cisco',
        '00:D0:5B': 'Cisco',
        '00:D0:5C': 'Cisco',
        '00:D0:5D': 'Cisco',
        '00:D0:5E': 'Cisco',
        '00:D0:5F': 'Cisco',
        '00:D0:60': 'Cisco',
        '00:D0:61': 'Cisco',
        '00:D0:62': 'Cisco',
        '00:D0:63': 'Cisco',
        '00:D0:64': 'Cisco',
        '00:D0:65': 'Cisco',
        '00:D0:66': 'Cisco',
        '00:D0:67': 'Cisco',
        '00:D0:68': 'Cisco',
        '00:D0:69': 'Cisco',
        '00:D0:6A': 'Cisco',
        '00:D0:6B': 'Cisco',
        '00:D0:6C': 'Cisco',
        '00:D0:6D': 'Cisco',
        '00:D0:6E': 'Cisco',
        '00:D0:6F': 'Cisco',
        '00:D0:70': 'Cisco',
        '00:D0:71': 'Cisco',
        '00:D0:72': 'Cisco',
        '00:D0:73': 'Cisco',
        '00:D0:74': 'Cisco',
        '00:D0:75': 'Cisco',
        '00:D0:76': 'Cisco',
        '00:D0:77': 'Cisco',
        '00:D0:78': 'Cisco',
        '00:D0:79': 'Cisco',
        '00:D0:7A': 'Cisco',
        '00:D0:7B': 'Cisco',
        '00:D0:7C': 'Cisco',
        '00:D0:7D': 'Cisco',
        '00:D0:7E': 'Cisco',
        '00:D0:7F': 'Cisco',
        '00:D0:80': 'Cisco',
        '00:D0:81': 'Cisco',
        '00:D0:82': 'Cisco',
        '00:D0:83': 'Cisco',
        '00:D0:84': 'Cisco',
        '00:D0:85': 'Cisco',
        '00:D0:86': 'Cisco',
        '00:D0:87': 'Cisco',
        '00:D0:88': 'Cisco',
        '00:D0:89': 'Cisco',
        '00:D0:8A': 'Cisco',
        '00:D0:8B': 'Cisco',
        '00:D0:8C': 'Cisco',
        '00:D0:8D': 'Cisco',
        '00:D0:8E': 'Cisco',
        '00:D0:8F': 'Cisco',
        '00:D0:90': 'Cisco',
        '00:D0:91': 'Cisco',
        '00:D0:92': 'Cisco',
        '00:D0:93': 'Cisco',
        '00:D0:94': 'Cisco',
        '00:D0:95': 'Cisco',
        '00:D0:96': 'Cisco',
        '00:D0:97': 'Cisco',
        '00:D0:98': 'Cisco',
        '00:D0:99': 'Cisco',
        '00:D0:9A': 'Cisco',
        '00:D0:9B': 'Cisco',
        '00:D0:9C': 'Cisco',
        '00:D0:9D': 'Cisco',
        '00:D0:9E': 'Cisco',
        '00:D0:9F': 'Cisco',
        '00:D0:A0': 'Cisco',
        '00:D0:A1': 'Cisco',
        '00:D0:A2': 'Cisco',
        '00:D0:A3': 'Cisco',
        '00:D0:A4': 'Cisco',
        '00:D0:A5': 'Cisco',
        '00:D0:A6': 'Cisco',
        '00:D0:A7': 'Cisco',
        '00:D0:A8': 'Cisco',
        '00:D0:A9': 'Cisco',
        '00:D0:AA': 'Cisco',
        '00:D0:AB': 'Cisco',
        '00:D0:AC': 'Cisco',
        '00:D0:AD': 'Cisco',
        '00:D0:AE': 'Cisco',
        '00:D0:AF': 'Cisco',
        '00:D0:B0': 'Cisco',
        '00:D0:B1': 'Cisco',
        '00:D0:B2': 'Cisco',
        '00:D0:B3': 'Cisco',
        '00:D0:B4': 'Cisco',
        '00:D0:B5': 'Cisco',
        '00:D0:B6': 'Cisco',
        '00:D0:B7': 'Cisco',
        '00:D0:B8': 'Cisco',
        '00:D0:B9': 'Cisco',
        '00:D0:BA': 'Cisco',
        '00:D0:BB': 'Cisco',
        '00:D0:BC': 'Cisco',
        '00:D0:BD': 'Cisco',
        '00:D0:BE': 'Cisco',
        '00:D0:BF': 'Cisco',
        '00:D0:C0': 'Cisco',
        '00:D0:C1': 'Cisco',
        '00:D0:C2': 'Cisco',
        '00:D0:C3': 'Cisco',
        '00:D0:C4': 'Cisco',
        '00:D0:C5': 'Cisco',
        '00:D0:C6': 'Cisco',
        '00:D0:C7': 'Cisco',
        '00:D0:C8': 'Cisco',
        '00:D0:C9': 'Cisco',
        '00:D0:CA': 'Cisco',
        '00:D0:CB': 'Cisco',
        '00:D0:CC': 'Cisco',
        '00:D0:CD': 'Cisco',
        '00:D0:CE': 'Cisco',
        '00:D0:CF': 'Cisco',
        '00:D0:D0': 'Cisco',
        '00:D0:D1': 'Cisco',
        '00:D0:D2': 'Cisco',
        '00:D0:D3': 'Cisco',
        '00:D0:D4': 'Cisco',
        '00:D0:D5': 'Cisco',
        '00:D0:D6': 'Cisco',
        '00:D0:D7': 'Cisco',
        '00:D0:D8': 'Cisco',
        '00:D0:D9': 'Cisco',
        '00:D0:DA': 'Cisco',
        '00:D0:DB': 'Cisco',
        '00:D0:DC': 'Cisco',
        '00:D0:DD': 'Cisco',
        '00:D0:DE': 'Cisco',
        '00:D0:DF': 'Cisco',
        '00:D0:E0': 'Cisco',
        '00:D0:E1': 'Cisco',
        '00:D0:E2': 'Cisco',
        '00:D0:E3': 'Cisco',
        '00:D0:E4': 'Cisco',
        '00:D0:E5': 'Cisco',
        '00:D0:E6': 'Cisco',
        '00:D0:E7': 'Cisco',
        '00:D0:E8': 'Cisco',
        '00:D0:E9': 'Cisco',
        '00:D0:EA': 'Cisco',
        '00:D0:EB': 'Cisco',
        '00:D0:EC': 'Cisco',
        '00:D0:ED': 'Cisco',
        '00:D0:EE': 'Cisco',
        '00:D0:EF': 'Cisco',
        '00:D0:F0': 'Cisco',
        '00:D0:F1': 'Cisco',
        '00:D0:F2': 'Cisco',
        '00:D0:F3': 'Cisco',
        '00:D0:F4': 'Cisco',
        '00:D0:F5': 'Cisco',
        '00:D0:F6': 'Cisco',
        '00:D0:F7': 'Cisco',
        '00:D0:F8': 'Cisco',
        '00:D0:F9': 'Cisco',
        '00:D0:FA': 'Cisco',
        '00:D0:FB': 'Cisco',
        '00:D0:FC': 'Cisco',
        '00:D0:FD': 'Cisco',
        '00:D0:FE': 'Cisco',
        '00:D0:FF': 'Cisco',
    }
    
    def __init__(self, timeout: int = 3, max_threads: int = 50, use_sophos: bool = True):
        self.timeout = timeout
        self.max_threads = max_threads
        self.sophos_scanner = None
        
        # Try to initialize Sophos scanner if available and requested
        if use_sophos and SOPHOS_AVAILABLE:
            try:
                self.sophos_scanner = SophosNetworkScanner()
                logger.info("Sophos scanner initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Sophos scanner: {e}")
                self.sophos_scanner = None
        
    def ping_host(self, host: str) -> bool:
        """Ping a host to check if it's online"""
        try:
            # Check OS to use correct ping command
            import platform
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            wait_param = '-w' if platform.system().lower() == 'windows' else '-W'
            timeout_val = str(self.timeout * 1000) if platform.system().lower() == 'windows' else str(self.timeout)
            
            result = subprocess.run(
                ['ping', param, '1', wait_param, timeout_val, host],
                capture_output=True,
                text=True,
                timeout=self.timeout + 1
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, Exception):
            return False
    
    def get_mac_address(self, host: str) -> Optional[str]:
        """Get MAC address for a host using ARP table"""
        try:
            result = subprocess.run(
                ['arp', '-a', host],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Parse ARP output to find MAC address
            for line in result.stdout.split('\n'):
                if host in line:
                    mac_match = re.search(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', line)
                    if mac_match:
                        return mac_match.group(0).upper().replace('-', ':')
        except Exception as e:
            logger.warning(f"Failed to get MAC address for {host}: {e}")
        return None
    
    def resolve_hostname(self, host: str) -> Optional[str]:
        """Resolve hostname for an IP address"""
        try:
            hostname = socket.gethostbyaddr(host)[0]
            return hostname
        except socket.herror:
            return None
        except Exception as e:
            logger.warning(f"Failed to resolve hostname for {host}: {e}")
            return None
    
    def scan_ports(self, host: str, ports: List[int] = None) -> Dict[int, bool]:
        """Scan specific ports on a host"""
        if ports is None:
            ports = self.COMMON_PORTS
            
        results = {}
        
        def scan_port(port):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.timeout)
                result = sock.connect_ex((host, port))
                sock.close()
                return port, result == 0
            except Exception:
                return port, False
        
        with ThreadPoolExecutor(max_workers=min(len(ports), 20)) as executor:
            future_to_port = {executor.submit(scan_port, port): port for port in ports}
            for future in as_completed(future_to_port):
                port, is_open = future.result()
                results[port] = is_open
                
        return results
    
    def identify_device_type(self, host: str, mac_address: str = None, open_ports: Dict[int, bool] = None) -> str:
        """Identify device type based on MAC address and open ports"""
        NetworkDevice = get_network_device_model()
        
        if mac_address:
            mac_prefix = mac_address[:8].upper().replace('-', ':')
            
            # Check vendor prefixes for device type
            vendor = self.VENDOR_PREFIXES.get(mac_prefix, '')
            
            if vendor in ['Apple', 'Samsung', 'Huawei', 'Xiaomi']:
                return NetworkDevice.TYPE_MOBILE
            elif vendor in ['HP', 'Lexmark', 'Brother', 'Canon']:
                return NetworkDevice.TYPE_PRINTER
            elif vendor in ['Cisco', 'Ubiquiti', 'TP-Link', 'MikroTik', 'D-Link']:
                return NetworkDevice.TYPE_SWITCH if open_ports and open_ports.get(161) else NetworkDevice.TYPE_ROUTER
            elif vendor in ['VMware', 'VirtualBox', 'Microsoft Hyper-V', 'Dell', 'Microsoft']:
                return NetworkDevice.TYPE_PC
            elif vendor in ['Synology', 'QNAP']:
                return NetworkDevice.TYPE_NAS
        
        if open_ports:
            # Identify based on open ports
            if open_ports.get(9100) or open_ports.get(515) or open_ports.get(631):  # Printer ports
                return NetworkDevice.TYPE_PRINTER
            
            if open_ports.get(5000) or open_ports.get(5001) or open_ports.get(8080): # NAS web interfaces
                if mac_address and ('Synology' in self.VENDOR_PREFIXES.get(mac_address[:8].upper(), '') or 
                                  'QNAP' in self.VENDOR_PREFIXES.get(mac_address[:8].upper(), '')):
                    return NetworkDevice.TYPE_NAS
                # Many NAS use 8080, but so do other things. Combined with 445 (SMB), it's more likely a NAS.
                if open_ports.get(445):
                    return NetworkDevice.TYPE_NAS
            
            if open_ports.get(135) or open_ports.get(445) or open_ports.get(3389):
                return NetworkDevice.TYPE_PC
                
            if open_ports.get(22) and open_ports.get(80):
                # Could be a router or a Linux PC
                return NetworkDevice.TYPE_ROUTER if open_ports.get(53) else NetworkDevice.TYPE_PC
            
            if open_ports.get(161):  # SNMP
                return NetworkDevice.TYPE_SWITCH
        
        return NetworkDevice.TYPE_UNKNOWN
    
    def scan_network(self, network_range: str) -> List[Dict]:
        """Scan a network range and return discovered devices"""
        
        # Use Sophos scanner if available and properly initialized
        if self.sophos_scanner:
            try:
                # Check if Sophos scanner is connected
                if hasattr(self.sophos_scanner, 'client') and self.sophos_scanner.client:
                    logger.info(f"Scanning network using Sophos firewall: {network_range}")
                    devices = self.sophos_scanner.scan_network(network_range)
                    logger.info(f"Sophos scanner found {len(devices)} devices")
                    # Only use Sophos results if it found devices
                    if devices:
                        return devices
                    else:
                        logger.info("Sophos scanner found no devices, falling back to ping scan")
                else:
                    logger.info("Sophos scanner not connected, using ping scan")
            except Exception as e:
                logger.error(f"Sophos scan failed, falling back to ping scan: {e}")
        
        # Always fallback to ping scanning
        logger.info(f"Scanning network using ping method: {network_range}")
        network = IPv4Network(network_range, strict=False)
        devices = []
        
        def scan_host(ip):
            try:
                ip_str = str(ip)
                if not self.ping_host(ip_str):
                    return None
                
                device_info = {
                    'ip_address': ip_str,
                    'mac_address': self.get_mac_address(ip_str),
                    'hostname': self.resolve_hostname(ip_str),
                    'open_ports': self.scan_ports(ip_str),
                }
                
                device_info['device_type'] = self.identify_device_type(
                    ip_str, 
                    device_info['mac_address'], 
                    device_info['open_ports']
                )
                
                # Generate a name if hostname is not available
                if not device_info['hostname']:
                    device_info['hostname'] = f"Device-{ip_str.split('.')[-1]}"
                
                # Set vendor based on MAC address
                if device_info['mac_address']:
                    mac_prefix = device_info['mac_address'][:8].upper()
                    device_info['vendor'] = self.VENDOR_PREFIXES.get(mac_prefix, 'Unknown')
                else:
                    device_info['vendor'] = 'Unknown'
                
                return device_info
                
            except Exception as e:
                logger.error(f"Error scanning {ip}: {e}")
                return None
        
        # Use ThreadPoolExecutor for parallel scanning
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = {executor.submit(scan_host, ip): ip for ip in network.hosts()}
            
            for future in as_completed(futures):
                try:
                    device_info = future.result()
                    if device_info:
                        devices.append(device_info)
                except Exception as e:
                    logger.error(f"Error in future: {e}")
        
        return devices
    
    def get_local_networks(self) -> List[str]:
        """Get local network ranges"""
        networks = []
        
        try:
            # Get local IP and subnet
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            
            # Extract network range from local IP
            ip_parts = local_ip.split('.')
            if len(ip_parts) == 4:
                # Create /24 network from local IP
                network_range = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/24"
                
                # Skip virtualization networks to avoid false positives
                skip_networks = ['192.168.56.0/24', '172.10.10.0/24', '192.168.53.0/24']
                
                if network_range not in skip_networks:
                    networks.append(network_range)
                
                # Also add some common ranges as fallback (excluding virtualization networks)
                common_ranges = [
                    '192.168.253.0/24',  # User's actual network
                    '192.168.254.0/24',  # Common for corporate networks
                    '192.168.1.0/24',
                    '192.168.0.0/24',
                    '10.0.0.0/24',
                    '172.16.0.0/24',
                ]
                
                # Skip virtualization networks to avoid false positives
                skip_networks = ['192.168.56.0/24', '172.10.10.0/24', '192.168.53.0/24']
                
                # Add ranges that aren't already included and aren't virtual networks
                for range_ip in common_ranges:
                    if range_ip not in networks and range_ip not in skip_networks:
                        networks.append(range_ip)
            else:
                # Fallback to common ranges if IP parsing fails
                networks = [
                    '192.168.253.0/24',
                    '192.168.1.0/24',
                    '192.168.0.0/24',
                    '10.0.0.0/24',
                ]
                
        except Exception as e:
            logger.error(f"Error getting local networks: {e}")
            # Fallback to common ranges including user's network (excluding virtual networks)
            networks = [
                '192.168.253.0/24',
                '192.168.254.0/24',
                '192.168.1.0/24',
                '192.168.0.0/24',
            ]
        
        return networks
