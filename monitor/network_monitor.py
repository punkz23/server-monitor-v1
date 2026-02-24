"""
Network monitoring module for SNMP and API polling
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import requests
from pysnmp.hlapi import (
    CommunityData,
    ContextData,
    ObjectType,
    ObjectIdentity,
    SnmpEngine,
    UdpTransportTarget,
    getCmd,
    nextCmd,
)

from .models import NetworkDevice, NetworkMetric, NetworkInterface, SecurityEvent, TrafficLog
from .services.network_scanner import NetworkScanner
from .alerts import evaluate_alerts_for_device

logger = logging.getLogger(__name__)


class SNMPMonitor:
    """SNMP monitoring for network devices"""
    
    # Common OIDs for network monitoring
    OIDS = {
        'system_description': '1.3.6.1.2.1.1.1.0',
        'system_uptime': '1.3.6.1.2.1.1.3.0',
        'cpu_usage': '1.3.6.1.4.1.2021.11.9.0',  # Net-SNMP
        'memory_total': '1.3.6.1.4.1.2021.4.5.0',  # Net-SNMP
        'memory_available': '1.3.6.1.4.1.2021.4.6.0',  # Net-SNMP
        'interface_count': '1.3.6.1.2.1.2.1.0',
        'interface_table': '1.3.6.1.2.1.2.2.1',  # ifTable
        'interface_name': '1.3.6.1.2.1.2.2.1.2',
        'interface_status': '1.3.6.1.2.1.2.2.1.8',
        'interface_speed': '1.3.6.1.2.1.2.2.1.5',
        'interface_in_octets': '1.3.6.1.2.1.2.2.1.10',
        'interface_out_octets': '1.3.6.1.2.1.2.2.1.16',
        'interface_in_packets': '1.3.6.1.2.1.2.2.1.11',
        'interface_out_packets': '1.3.6.1.2.1.2.2.1.17',
    }
    
    def __init__(self, device: NetworkDevice):
        self.device = device
        self.community = device.snmp_community
        self.port = device.snmp_port
        self.ip = str(device.ip_address)
    
    def get_single_oid(self, oid: str) -> Optional[str]:
        """Get a single OID value"""
        try:
            error_indication, error_status, error_index, var_binds = next(
                getCmd(
                    SnmpEngine(),
                    CommunityData(self.community),
                    UdpTransportTarget((self.ip, self.port)),
                    ContextData(),
                    ObjectType(ObjectIdentity(oid)),
                )
            )
            
            if error_indication:
                logger.error(f"SNMP error for {self.device.name}: {error_indication}")
                return None
            elif error_status:
                logger.error(f"SNMP error for {self.device.name}: {error_status}")
                return None
            else:
                for var_bind in var_binds:
                    return str(var_bind[1])
        except Exception as e:
            logger.error(f"SNMP exception for {self.device.name}: {e}")
            return None
    
    def walk_oid(self, oid: str) -> List[Tuple[str, str]]:
        """Walk through an OID table"""
        results = []
        try:
            iterator = nextCmd(
                SnmpEngine(),
                CommunityData(self.community),
                UdpTransportTarget((self.ip, self.port)),
                ContextData(),
                ObjectType(ObjectIdentity(oid)),
                lexicographicMode=False,
            )
            
            for error_indication, error_status, error_index, var_binds in iterator:
                if error_indication:
                    break
                elif error_status:
                    break
                else:
                    for var_bind in var_binds:
                        results.append((str(var_bind[0]), str(var_bind[1])))
        except Exception as e:
            logger.error(f"SNMP walk exception for {self.device.name}: {e}")
        
        return results
    
    def collect_system_metrics(self) -> Dict[str, float]:
        """Collect system performance metrics"""
        metrics = {}
        
        # CPU usage (if available)
        cpu_raw = self.get_single_oid(self.OIDS['cpu_usage'])
        if cpu_raw:
            try:
                metrics['cpu_usage'] = float(cpu_raw)
            except ValueError:
                pass
        
        # Memory metrics
        mem_total = self.get_single_oid(self.OIDS['memory_total'])
        mem_avail = self.get_single_oid(self.OIDS['memory_available'])
        
        if mem_total and mem_avail:
            try:
                total_kb = float(mem_total)
                avail_kb = float(mem_avail)
                if total_kb > 0:
                    used_kb = total_kb - avail_kb
                    metrics['memory_usage'] = (used_kb / total_kb) * 100
                    metrics['memory_total_mb'] = total_kb / 1024
                    metrics['memory_available_mb'] = avail_kb / 1024
            except ValueError:
                pass
        
        # System uptime
        uptime_raw = self.get_single_oid(self.OIDS['system_uptime'])
        if uptime_raw:
            try:
                uptime_ticks = int(uptime_raw.split('(')[0])
                metrics['uptime_days'] = uptime_ticks / 86400000  # Convert to days
            except (ValueError, IndexError):
                pass
        
        return metrics
    
    def collect_interface_data(self) -> List[Dict]:
        """Collect network interface data"""
        interfaces = []
        
        # Get interface table
        interface_data = {}
        for oid_type in ['name', 'status', 'speed', 'in_octets', 'out_octets', 'in_packets', 'out_packets']:
            oid = self.OIDS[f'interface_{oid_type}']
            results = self.walk_oid(oid)
            for full_oid, value in results:
                # Extract interface index from OID
                parts = full_oid.split('.')
                if len(parts) > 0:
                    if_index = parts[-1]
                    if if_index not in interface_data:
                        interface_data[if_index] = {}
                    interface_data[if_index][oid_type] = value
        
        # Process interface data
        for if_index, data in interface_data.items():
            if 'name' in data:
                interface = {
                    'name': data['name'],
                    'index': if_index,
                    'status': 'up' if data.get('status') == '1' else 'down',
                }
                
                # Add numeric values
                for field in ['speed', 'in_octets', 'out_octets', 'in_packets', 'out_packets']:
                    if field in data:
                        try:
                            interface[field] = int(data[field])
                        except ValueError:
                            interface[field] = 0
                
                interfaces.append(interface)
        
        return interfaces
    
    def update_device_metrics(self):
        """Update device metrics in database"""
        if not self.device.enabled:
            return
        
        # Collect system metrics
        system_metrics = self.collect_system_metrics()
        for metric_name, value in system_metrics.items():
            unit = '%' if 'usage' in metric_name else ('days' if 'days' in metric_name else 'MB')
            NetworkMetric.objects.create(
                device=self.device,
                metric_name=metric_name,
                value=value,
                unit=unit
            )
        
        # Collect interface data
        interfaces = self.collect_interface_data()
        for interface_data in interfaces:
            # Update or create interface record
            interface, created = NetworkInterface.objects.get_or_create(
                device=self.device,
                name=interface_data['name'],
                defaults={
                    'status': interface_data['status'],
                    'speed': interface_data.get('speed'),
                }
            )
            
            if not created:
                interface.status = interface_data['status']
                if 'speed' in interface_data:
                    interface.speed = interface_data['speed']
                interface.save()
            
            # Create traffic log
            TrafficLog.objects.create(
                interface=interface,
                bytes_in=interface_data.get('in_octets', 0),
                bytes_out=interface_data.get('out_octets', 0),
                packets_in=interface_data.get('in_packets', 0),
                packets_out=interface_data.get('out_packets', 0),
            )
        
        # Update last checked timestamp
        self.device.last_checked = datetime.now()
        self.device.save()


class SophosAPI:
    """Sophos XGS Firewall API integration"""
    
    def __init__(self, device: NetworkDevice):
        self.device = device
        self.base_url = f"https://{device.ip_address}:{device.api_port}"
        self.token = device.api_token
        self.session = requests.Session()
        if self.token:
            self.session.headers.update({'Authorization': f'Bearer {self.token}'})
        self.session.verify = False  # For self-signed certificates
    
    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            response = self.session.get(f"{self.base_url}/webconsole/api/v1/system/info", timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"API connection test failed for {self.device.name}: {e}")
            return False
    
    def get_system_info(self) -> Dict:
        """Get system information"""
        try:
            response = self.session.get(f"{self.base_url}/webconsole/api/v1/system/info", timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get system info for {self.device.name}: {e}")
        return {}
    
    def get_firewall_rules(self) -> List[Dict]:
        """Get firewall rules"""
        try:
            response = self.session.get(f"{self.base_url}/webconsole/api/v1/firewall/rules", timeout=10)
            if response.status_code == 200:
                return response.json().get('rules', [])
        except Exception as e:
            logger.error(f"Failed to get firewall rules for {self.device.name}: {e}")
        return []
    
    def get_security_events(self, limit: int = 100) -> List[Dict]:
        """Get security events"""
        try:
            response = self.session.get(f"{self.base_url}/webconsole/api/v1/reporting/events", 
                                     params={'limit': limit}, timeout=10)
            if response.status_code == 200:
                return response.json().get('events', [])
        except Exception as e:
            logger.error(f"Failed to get security events for {self.device.name}: {e}")
        return []
    
    def update_security_events(self):
        """Update security events in database"""
        if not self.device.enabled or not self.token:
            return
        
        events = self.get_security_events(50)
        for event in events:
            SecurityEvent.objects.create(
                device=self.device,
                event_type=event.get('type', 'unknown'),
                source_ip=event.get('source_ip'),
                dest_ip=event.get('dest_ip'),
                source_port=event.get('source_port'),
                dest_port=event.get('dest_port'),
                protocol=event.get('protocol'),
                action=event.get('action'),
                rule_name=event.get('rule_name'),
                severity=event.get('severity', 'medium'),
            )


def monitor_all_devices():
    """Monitor all enabled network devices"""
    devices = NetworkDevice.objects.filter(enabled=True)
    scanner = NetworkScanner()
    
    for device in devices:
        try:
            # 1. Ping check for UP/DOWN status
            is_up = scanner.ping_host(str(device.ip_address))
            new_status = "UP" if is_up else "DOWN"
            
            # Check if status changed
            status_changed = (device.last_status != new_status)
            device.last_status = new_status
            device.is_active = is_up
            device.last_checked = datetime.now()
            device.save(update_fields=['last_status', 'is_active', 'last_checked'])
            
            # 2. SNMP monitoring (only if device is UP)
            if is_up:
                try:
                    snmp_monitor = SNMPMonitor(device)
                    snmp_monitor.update_device_metrics()
                except Exception as e:
                    logger.error(f"SNMP monitoring failed for {device.name}: {e}")
            
            # 3. API monitoring (if token is configured and device is UP)
            if is_up and device.api_token:
                try:
                    api = SophosAPI(device)
                    api.update_security_events()
                except Exception as e:
                    logger.error(f"API monitoring failed for {device.name}: {e}")
            
            # 4. Evaluate alerts
            evaluate_alerts_for_device(device)
            
            logger.info(f"Successfully monitored {device.name} - Status: {new_status}")
        except Exception as e:
            logger.error(f"Failed to monitor {device.name}: {e}")
