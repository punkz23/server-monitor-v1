"""
Network Bandwidth Monitoring Service

This service provides multiple methods to monitor network bandwidth usage for devices:
1. SNMP-based monitoring for managed devices (switches, routers, firewalls)
2. ARP table monitoring for basic traffic estimation
3. NetFlow/sFlow support (future enhancement)
"""

import subprocess
import time
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import socket
import struct
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class BandwidthData:
    """Bandwidth measurement data"""
    device_ip: str
    bytes_in: int
    bytes_out: int
    packets_in: int
    packets_out: int
    timestamp: datetime
    interface: Optional[str] = None

class BandwidthMonitor:
    """Network bandwidth monitoring service"""
    
    def __init__(self):
        self.snmp_community = 'public'  # Default SNMP community
        self.snmp_timeout = 5
        self.arp_cache = {}
        self.last_traffic_data = {}
        
    def get_device_bandwidth_via_snmp(self, device_ip: str, interface_index: Optional[str] = None) -> Optional[BandwidthData]:
        """
        Get bandwidth data via SNMP for managed devices
        Requires SNMP to be enabled on the target device
        """
        try:
            # SNMP OIDs for interface statistics
            if_octets_in = '1.3.6.1.2.1.2.2.1.10'  # ifInOctets
            if_octets_out = '1.3.6.1.2.1.2.2.1.16'  # ifOutOctets
            if_packets_in = '1.3.6.1.2.1.2.2.1.11'  # ifInUcastPkts
            if_packets_out = '1.3.6.1.2.1.2.2.1.17'  # ifOutUcastPkts
            
            # Get interface list if not specified
            if not interface_index:
                interface_index = self._get_primary_interface(device_ip)
                if not interface_index:
                    return None
            
            # Get interface statistics
            bytes_in = self._snmp_get(device_ip, f"{if_octets_in}.{interface_index}")
            bytes_out = self._snmp_get(device_ip, f"{if_octets_out}.{interface_index}")
            packets_in = self._snmp_get(device_ip, f"{if_packets_in}.{interface_index}")
            packets_out = self._snmp_get(device_ip, f"{if_packets_out}.{interface_index}")
            
            if all(x is not None for x in [bytes_in, bytes_out, packets_in, packets_out]):
                return BandwidthData(
                    device_ip=device_ip,
                    bytes_in=int(bytes_in),
                    bytes_out=int(bytes_out),
                    packets_in=int(packets_in),
                    packets_out=int(packets_out),
                    timestamp=datetime.now(),
                    interface=interface_index
                )
                
        except Exception as e:
            logger.error(f"SNMP query failed for {device_ip}: {e}")
            
        return None
    
    def get_arp_table_traffic(self) -> Dict[str, Dict]:
        """
        Get basic traffic estimation from ARP table
        This is a very basic method and may not be accurate
        """
        try:
            # Get ARP table
            result = subprocess.run(['arp', '-a'], capture_output=True, text=True, timeout=10)
            
            traffic_data = {}
            current_time = datetime.now()
            
            for line in result.stdout.split('\n'):
                if 'dynamic' in line.lower() or 'static' in line.lower():
                    # Parse ARP entry
                    match = re.search(r'(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F:-]+)', line)
                    if match:
                        ip = match.group(1)
                        mac = match.group(2)
                        
                        # Simple activity detection (this is very basic)
                        if ip not in self.arp_cache:
                            self.arp_cache[ip] = {'first_seen': current_time, 'last_seen': current_time}
                        else:
                            self.arp_cache[ip]['last_seen'] = current_time
                            
                        traffic_data[ip] = {
                            'mac': mac,
                            'last_seen': self.arp_cache[ip]['last_seen'],
                            'active': (current_time - self.arp_cache[ip]['last_seen']).seconds < 300
                        }
            
            return traffic_data
            
        except Exception as e:
            logger.error(f"Failed to get ARP table: {e}")
            return {}
    
    def get_interface_bandwidth_via_netstat(self) -> Dict[str, BandwidthData]:
        """
        Get local interface bandwidth statistics
        This works for the monitoring server itself
        """
        try:
            bandwidth_data = {}
            
            # Get network interface statistics
            result = subprocess.run(['netstat', '-e'], capture_output=True, text=True, timeout=10)
            
            lines = result.stdout.split('\n')
            headers = None
            
            for line in lines:
                if 'Bytes' in line:
                    headers = line.split()
                elif headers and line.strip():
                    parts = line.split()
                    if len(parts) >= len(headers):
                        interface_name = parts[0]
                        
                        try:
                            bytes_received = int(parts[1].replace(',', ''))
                            bytes_sent = int(parts[2].replace(',', ''))
                            packets_received = int(parts[3].replace(',', ''))
                            packets_sent = int(parts[4].replace(',', ''))
                            
                            bandwidth_data[interface_name] = BandwidthData(
                                device_ip=socket.gethostbyname(socket.gethostname()),
                                bytes_in=bytes_received,
                                bytes_out=bytes_sent,
                                packets_in=packets_received,
                                packets_out=packets_sent,
                                timestamp=datetime.now(),
                                interface=interface_name
                            )
                        except (ValueError, IndexError):
                            continue
            
            return bandwidth_data
            
        except Exception as e:
            logger.error(f"Failed to get netstat data: {e}")
            return {}
    
    def calculate_bandwidth_rate(self, current_data: BandwidthData, previous_data: BandwidthData) -> Dict[str, float]:
        """
        Calculate bandwidth rate between two measurements
        Returns rates in bits per second
        """
        if not previous_data:
            return {'bps_in': 0, 'bps_out': 0, 'pps_in': 0, 'pps_out': 0}
        
        time_diff = (current_data.timestamp - previous_data.timestamp).total_seconds()
        if time_diff <= 0:
            return {'bps_in': 0, 'bps_out': 0, 'pps_in': 0, 'pps_out': 0}
        
        bytes_diff = current_data.bytes_in - previous_data.bytes_in
        packets_diff = current_data.packets_in - previous_data.packets_in
        
        bps_in = (bytes_diff * 8) / time_diff if bytes_diff > 0 else 0
        bps_out = ((current_data.bytes_out - previous_data.bytes_out) * 8) / time_diff if (current_data.bytes_out - previous_data.bytes_out) > 0 else 0
        pps_in = packets_diff / time_diff if packets_diff > 0 else 0
        pps_out = (current_data.packets_out - previous_data.packets_out) / time_diff if (current_data.packets_out - previous_data.packets_out) > 0 else 0
        
        return {
            'bps_in': bps_in,
            'bps_out': bps_out,
            'total_bps': bps_in + bps_out,
            'pps_in': pps_in,
            'pps_out': pps_out,
            'total_pps': pps_in + pps_out
        }
    
    def _snmp_get(self, host: str, oid: str) -> Optional[str]:
        """Perform SNMP GET request"""
        try:
            result = subprocess.run([
                'snmpget', '-v2c', '-c', self.snmp_community,
                '-t', str(self.snmp_timeout),
                host, oid
            ], capture_output=True, text=True, timeout=self.snmp_timeout + 5)
            
            if result.returncode == 0:
                # Extract value from SNMP response
                parts = result.stdout.strip().split()
                if len(parts) >= 3:
                    return parts[-1].strip('"')
            
        except FileNotFoundError:
            logger.warning("SNMP tools not found. Install net-snmp tools.")
        except Exception as e:
            logger.error(f"SNMP query failed: {e}")
        
        return None
    
    def _get_primary_interface(self, device_ip: str) -> Optional[str]:
        """Get primary interface index for a device"""
        try:
            # Get interface descriptions
            result = subprocess.run([
                'snmpwalk', '-v2c', '-c', self.snmp_community,
                '-t', str(self.snmp_timeout),
                device_ip, '1.3.6.1.2.1.2.2.1.2'  # ifDescr
            ], capture_output=True, text=True, timeout=self.snmp_timeout + 10)
            
            if result.returncode == 0:
                # Look for common interface names
                for line in result.stdout.split('\n'):
                    if any(name in line.lower() for name in ['ethernet', 'gigabit', 'fastethernet', 'wan', 'lan']):
                        # Extract interface index
                        match = re.search(r'(\d+\.\d+\.\d+\.\d+\.\d+)', line)
                        if match:
                            return match.group(1).split('.')[-1]
            
            # Fallback to first interface
            first_line = result.stdout.split('\n')[0] if result.stdout else ''
            match = re.search(r'(\d+\.\d+\.\d+\.\d+\.\d+)', first_line)
            if match:
                return match.group(1).split('.')[-1]
                
        except Exception as e:
            logger.error(f"Failed to get interfaces for {device_ip}: {e}")
        
        return None
    
    def monitor_device_bandwidth(self, device_ip: str, method: str = 'auto') -> Optional[BandwidthData]:
        """
        Monitor bandwidth for a specific device
        Method can be: 'snmp', 'arp', 'netstat', or 'auto'
        """
        if method == 'auto':
            # Try SNMP first, then fallback
            data = self.get_device_bandwidth_via_snmp(device_ip)
            if data:
                return data
            
            # For local host, try netstat
            if device_ip in ['127.0.0.1', socket.gethostbyname(socket.gethostname())]:
                local_data = self.get_interface_bandwidth_via_netstat()
                if local_data:
                    return list(local_data.values())[0]  # Return first interface
        
        elif method == 'snmp':
            return self.get_device_bandwidth_via_snmp(device_ip)
        
        elif method == 'netstat':
            local_data = self.get_interface_bandwidth_via_netstat()
            if local_data:
                return list(local_data.values())[0]
        
        return None
    
    def get_top_bandwidth_consumers(self, limit: int = 10) -> List[Dict]:
        """
        Get top bandwidth consumers based on recent measurements
        This would require storing historical data in the database
        """
        # This is a placeholder - in a real implementation, you would:
        # 1. Query the database for recent bandwidth measurements
        # 2. Calculate average bandwidth usage per device
        # 3. Return top consumers
        
        return []
