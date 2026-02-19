import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from ..models import NetworkDevice, NetworkMetric, NetworkInterface, SecurityEvent, DeviceBandwidthUsage
from ..sophos_xml_parser import SophosXMLParser

logger = logging.getLogger(__name__)

class SophosMonitoringService:
    """Service for monitoring Sophos XGS126 devices"""
    
    def __init__(self, device):
        """Initialize with a NetworkDevice instance"""
        self.device = device
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize the Sophos API client"""
        from ..sophos import SophosXGS126Client
        
        try:
            self.client = SophosXGS126Client(
                host=self.device.ip_address,
                port=self.device.api_port,
                username=self.device.api_username,
                password=self.device.api_token
            )
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Sophos client for {self.device.name}: {str(e)}")
            return False
    
    def update_device_status(self):
        """Update all device metrics and status"""
        if not self.client:
            if not self._init_client():
                return False
        
        try:
            # Update basic device info
            self._update_system_status()
            
            # Update interfaces
            self._update_interfaces()
            
            # Update metrics
            self._update_metrics()
            
            # Update security events
            self._update_security_events()
            
            # Update bandwidth usage
            self._update_bandwidth_usage()
            
            # Update last checked timestamp
            self.device.last_checked = timezone.now()
            self.device.save(update_fields=['last_checked'])
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating device {self.device.name}: {str(e)}")
            return False
    
    def _update_system_status(self):
        """Update system status and basic metrics"""
        system_status = self.client.get_system_status()
        resources = self.client.get_system_resources()
        
        # Parse system status XML
        if isinstance(system_status, str) and system_status.strip().startswith('<?xml'):
            parsed_status = SophosXMLParser.parse_system_status(system_status)
            if parsed_status:
                # Only update fields that exist in the model
                # Note: NetworkDevice doesn't have firmware_version, serial_number, model fields
                # These would need to be added to the model if we want to store them
                logger.debug(f"Parsed system status (fields not in model): {parsed_status}")
        
        # Parse system resources XML
        metrics = []
        if isinstance(resources, str) and resources.strip().startswith('<?xml'):
            parsed_resources = SophosXMLParser.parse_system_resources(resources)
            if parsed_resources:
                metrics = [
                    ('cpu_usage', parsed_resources.get('cpu_usage', 0), '%'),
                    ('memory_usage', parsed_resources.get('memory_usage', 0), '%'),
                    ('disk_usage', parsed_resources.get('disk_usage', 0), '%'),
                    ('temperature', parsed_resources.get('temperature', 0), '°C'),
                ]
                logger.debug(f"Parsed resource metrics: {parsed_resources}")
        elif isinstance(resources, dict):
            # Handle JSON responses (if any)
            metrics = [
                ('cpu_usage', resources.get('cpu_usage', 0), '%'),
                ('memory_usage', resources.get('memory_usage', 0), '%'),
                ('disk_usage', resources.get('disk_usage', 0), '%'),
            ]
        else:
            # Default metrics if we can't parse the response
            metrics = [
                ('cpu_usage', 0, '%'),
                ('memory_usage', 0, '%'),
                ('disk_usage', 0, '%'),
            ]
        
        self._save_metrics(metrics)
    
    def _update_interfaces(self):
        """Update network interfaces status"""
        interfaces = self.client.get_interfaces()
        
        # Parse interfaces XML
        if isinstance(interfaces, str) and interfaces.strip().startswith('<?xml'):
            parsed_interfaces = SophosXMLParser.parse_interfaces(interfaces)
            if parsed_interfaces:
                for iface_data in parsed_interfaces:
                    iface_name = iface_data.get('name') or iface_data.get('interface', '')
                    if not iface_name:
                        continue
                    
                    # Get or create interface
                    interface, created = NetworkInterface.objects.get_or_create(
                        device=self.device,
                        name=iface_name,
                        defaults={
                            'status': 'unknown',
                            'speed': 0,
                            'mtu': 1500,
                            'ip_address': iface_data.get('ip_address', ''),
                            'mac_address': iface_data.get('mac_address', '')
                        }
                    )
                    
                    if not created:
                        # Update existing interface
                        interface.status = iface_data.get('status', 'unknown')
                        interface.speed = int(iface_data.get('speed', 0))
                        interface.mtu = int(iface_data.get('mtu', 1500))
                        interface.ip_address = iface_data.get('ip_address', '')
                        interface.mac_address = iface_data.get('mac_address', '')
                        interface.save()
                
                logger.debug(f"Updated {len(parsed_interfaces)} interfaces")
                return
        
        # Handle JSON responses (if any)
        if isinstance(interfaces, list):
            existing_ifaces = {iface.name: iface for iface in self.device.interfaces.all()}
            
            for iface_data in interfaces:
                iface_name = iface_data.get('name')
                if not iface_name:
                    continue
                    
                iface = existing_ifaces.get(iface_name)
                if not iface:
                    iface = NetworkInterface(device=self.device, name=iface_name)
                
                # Update interface properties
                iface.status = 'up' if iface_data.get('status') == '1' else 'down'
                iface.speed = int(iface_data.get('speed', 0))
                iface.mtu = int(iface_data.get('mtu', 1500))
                iface.ip_address = iface_data.get('ip_address', '')
                iface.mac_address = iface_data.get('mac_address', '')
                iface.save()
                
                # Record interface metrics
                metrics = [
                    (f'iface_{iface_name}_rx_bytes', iface_data.get('rx_bytes', 0), 'bytes'),
                    (f'iface_{iface_name}_tx_bytes', iface_data.get('tx_bytes', 0), 'bytes'),
                    (f'iface_{iface_name}_rx_errors', iface_data.get('rx_errors', 0), 'count'),
                    (f'iface_{iface_name}_tx_errors', iface_data.get('tx_errors', 0), 'count')
                ]
                
                self._save_metrics(metrics)
    
    def _update_metrics(self):
        """Update various device metrics"""
        # Get VPN status
        vpn_status = self.client.get_vpn_status()
        # Get firewall stats
        fw_stats = self.client.get_firewall_sessions()
        
        vpn_up = 0
        fw_sessions = 0
        fw_throughput = 0
        threats_blocked = 0
        
        # Parse VPN XML responses
        if isinstance(vpn_status, str) and vpn_status.strip().startswith('<?xml'):
            parsed_vpn = SophosXMLParser.parse_vpn_status(vpn_status)
            if parsed_vpn:
                vpn_up = parsed_vpn.get('active_tunnels', 0)
                logger.debug(f"Parsed VPN status: {vpn_up} active tunnels")
        elif isinstance(vpn_status, dict):
            vpn_up = sum(1 for tunnel in vpn_status.get('tunnels', []) if tunnel.get('status') == 'up')
        
        # Parse firewall sessions XML responses
        if isinstance(fw_stats, str) and fw_stats.strip().startswith('<?xml'):
            parsed_fw = SophosXMLParser.parse_firewall_sessions(fw_stats)
            if parsed_fw:
                fw_sessions = parsed_fw.get('active_sessions', 0)
                # Use Mbps value if available, otherwise fallback to bps
                if 'throughput_mbps' in parsed_fw:
                    fw_throughput = parsed_fw.get('throughput_mbps', 0)
                    throughput_unit = 'Mbps'
                else:
                    fw_throughput = parsed_fw.get('throughput_bps', 0)
                    throughput_unit = 'bps'
                threats_blocked = parsed_fw.get('threats_blocked', 0)
                logger.debug(f"Parsed firewall stats: {parsed_fw}")
        elif isinstance(fw_stats, dict):
            fw_sessions = fw_stats.get('active_sessions', 0)
            fw_throughput = fw_stats.get('throughput_bps', 0)
            throughput_unit = 'bps'
            threats_blocked = fw_stats.get('threats_blocked_24h', 0)
        else:
            fw_sessions = 0
            fw_throughput = 0
            throughput_unit = 'Mbps'
            threats_blocked = 0
        
        metrics = [
            ('vpn_tunnels_up', vpn_up, 'count'),
            ('firewall_sessions', fw_sessions, 'sessions'),
            ('firewall_throughput', fw_throughput, throughput_unit),
            ('threats_blocked', threats_blocked, 'count')
        ]
        
        self._save_metrics(metrics)
    
    def _update_security_events(self):
        """Update security events from the firewall"""
        events = self.client.get_security_events(limit=50)
        
        # Parse security events XML
        if isinstance(events, str) and events.strip().startswith('<?xml'):
            parsed_events = SophosXMLParser.parse_security_events(events)
            if parsed_events:
                for event_data in parsed_events:
                    # Create security event from parsed XML data
                    SecurityEvent.objects.get_or_create(
                        device=self.device,
                        event_type=event_data.get('eventtype', 'security'),
                        source_ip=event_data.get('sourceip', ''),
                        dest_ip=event_data.get('destip', ''),
                        action=event_data.get('action', 'allow'),
                        severity=event_data.get('severity', 'medium'),
                        timestamp=timezone.now(),  # Use current time since XML may not have timestamp
                        defaults={
                            'rule_name': event_data.get('rulename', ''),
                            'protocol': event_data.get('protocol', ''),
                            'source_port': int(event_data.get('sourceport', 0)) if event_data.get('sourceport') else None,
                            'dest_port': int(event_data.get('destport', 0)) if event_data.get('destport') else None
                        }
                    )
                logger.debug(f"Created {len(parsed_events)} security events from XML")
                return
        
        # Handle JSON responses (if any)
        if isinstance(events, list):
            for event in events:
                SecurityEvent.objects.get_or_create(
                    device=self.device,
                    event_type=event.get('type', 'security'),
                    source_ip=event.get('source_ip', ''),
                    dest_ip=event.get('destination_ip', ''),
                    action=event.get('action', 'allow'),
                    severity=event.get('severity', 'medium'),
                    timestamp=event.get('timestamp') or timezone.now(),
                    defaults={
                        'rule_name': event.get('rule_name', ''),
                        'protocol': event.get('protocol', ''),
                        'source_port': event.get('source_port'),
                        'dest_port': event.get('dest_port')
                    }
                )
    
    def _update_bandwidth_usage(self):
        """Update per-IP bandwidth usage from security logs"""
        try:
            # Get recent security logs for bandwidth analysis
            logs = self.client.get_security_events(limit=200)  # Get more logs for bandwidth analysis
            
            # Parse bandwidth usage from logs
            if isinstance(logs, str) and logs.strip().startswith('<?xml'):
                bandwidth_entries = SophosXMLParser.parse_bandwidth_usage(logs)
                if bandwidth_entries:
                    self._save_bandwidth_usage(bandwidth_entries)
                    logger.debug(f"Processed {len(bandwidth_entries)} bandwidth entries")
                    return
            
            # Handle JSON responses (if any)
            elif isinstance(logs, list):
                # Convert JSON logs to bandwidth entries format
                bandwidth_entries = []
                for log in logs:
                    if log.get('source_ip') and (log.get('bytes_sent', 0) > 0 or log.get('bytes_received', 0) > 0):
                        bandwidth_entries.append({
                            'source_ip': log.get('source_ip'),
                            'dest_ip': log.get('dest_ip', ''),
                            'bytes_transferred': log.get('bytes_sent', 0) + log.get('bytes_received', 0),
                            'packets': log.get('packets_sent', 0) + log.get('packets_received', 0),
                            'protocol': log.get('protocol', 'unknown'),
                            'action': log.get('action', 'allow'),
                            'timestamp': log.get('timestamp', timezone.now().isoformat())
                        })
                
                if bandwidth_entries:
                    self._save_bandwidth_usage(bandwidth_entries)
                    logger.debug(f"Processed {len(bandwidth_entries)} bandwidth entries from JSON")
                    
        except Exception as e:
            logger.error(f"Error updating bandwidth usage: {e}")
    
    def _save_bandwidth_usage(self, bandwidth_entries):
        """Save bandwidth usage data to database"""
        with transaction.atomic():
            for entry in bandwidth_entries:
                source_ip = entry.get('source_ip')
                dest_ip = entry.get('dest_ip')
                bytes_transferred = entry.get('bytes_transferred', 0)
                packets = entry.get('packets', 0)
                protocol = entry.get('protocol', 'unknown')
                
                if not source_ip or bytes_transferred <= 0:
                    continue
                
                # Get or create bandwidth usage record
                bandwidth_usage, created = DeviceBandwidthUsage.objects.get_or_create(
                    device=self.device,
                    source_ip=source_ip,
                    dest_ip=dest_ip or 'unknown',
                    defaults={
                        'bytes_sent': bytes_transferred,
                        'packets_sent': packets,
                        'connections': 1,
                        'protocols': [protocol] if protocol != 'unknown' else []
                    }
                )
                
                if not created:
                    # Update existing record
                    bandwidth_usage.bytes_sent += bytes_transferred
                    bandwidth_usage.packets_sent += packets
                    bandwidth_usage.connections += 1
                    if protocol != 'unknown' and protocol not in bandwidth_usage.protocols:
                        bandwidth_usage.protocols.append(protocol)
                        bandwidth_usage.save(update_fields=['protocols'])
                    else:
                        bandwidth_usage.save(update_fields=['bytes_sent', 'packets_sent', 'connections'])
                
                logger.debug(f"Updated bandwidth usage for {source_ip}: +{bytes_transferred} bytes")
    
    def _save_metrics(self, metrics_data):
        """Save multiple metrics to the database"""
        timestamp = timezone.now()
        metrics = [
            NetworkMetric(
                device=self.device,
                metric_name=name,
                value=value,
                unit=unit,
                timestamp=timestamp
            )
            for name, value, unit in metrics_data
            if value is not None
        ]
        
        if metrics:
            NetworkMetric.objects.bulk_create(metrics)
    
    def get_top_bandwidth_consumers(self, limit=10, time_period_hours=24):
        """Get top bandwidth consumers by IP address"""
        from datetime import timedelta
        
        cutoff_time = timezone.now() - timedelta(hours=time_period_hours)
        
        top_consumers = DeviceBandwidthUsage.objects.filter(
            device=self.device,
            last_seen__gte=cutoff_time
        ).order_by('-bytes_sent')[:limit]
        
        results = []
        for consumer in top_consumers:
            # Try to find the device in the network devices
            device_info = None
            try:
                device_info = NetworkDevice.objects.get(ip_address=consumer.source_ip)
                device_name = device_info.name
                device_type = device_info.device_type
                hostname = device_info.hostname
            except NetworkDevice.DoesNotExist:
                device_name = f"Unknown ({consumer.source_ip})"
                device_type = "UNKNOWN"
                hostname = None
            
            results.append({
                'ip_address': consumer.source_ip,
                'device_name': device_name,
                'device_type': device_type,
                'hostname': hostname,
                'bytes_sent': consumer.bytes_sent,
                'bytes_received': consumer.bytes_received,
                'total_bytes': consumer.total_bytes,
                'packets_sent': consumer.packets_sent,
                'packets_received': consumer.packets_received,
                'total_packets': consumer.total_packets,
                'connections': consumer.connections,
                'protocols': consumer.protocols,
                'last_seen': consumer.last_seen,
                'first_seen': consumer.first_seen
            })
        
        return results
    
    def get_bandwidth_by_ip_range(self, ip_range=None, time_period_hours=24):
        """Get bandwidth usage for specific IP range or all IPs"""
        from datetime import timedelta
        from ipaddress import ip_network, ip_address
        
        cutoff_time = timezone.now() - timedelta(hours=time_period_hours)
        
        queryset = DeviceBandwidthUsage.objects.filter(
            device=self.device,
            last_seen__gte=cutoff_time
        )
        
        if ip_range:
            try:
                network = ip_network(ip_range, strict=False)
                # Filter IPs within the specified range
                filtered_ips = []
                for usage in queryset:
                    try:
                        if ip_address(usage.source_ip) in network:
                            filtered_ips.append(usage.id)
                    except ValueError:
                        continue
                queryset = DeviceBandwidthUsage.objects.filter(id__in=filtered_ips)
            except ValueError:
                logger.error(f"Invalid IP range: {ip_range}")
                return []
        
        results = []
        for usage in queryset.order_by('-bytes_sent'):
            results.append({
                'ip_address': usage.source_ip,
                'dest_ip': usage.dest_ip,
                'bytes_sent': usage.bytes_sent,
                'bytes_received': usage.bytes_received,
                'total_bytes': usage.total_bytes,
                'packets_sent': usage.packets_sent,
                'packets_received': usage.packets_received,
                'connections': usage.connections,
                'protocols': usage.protocols,
                'last_seen': usage.last_seen
            })
        
        return results
    
    def get_bandwidth_summary(self, time_period_hours=24):
        """Get summary statistics for bandwidth usage"""
        from datetime import timedelta
        from django.db.models import Sum, Count, Avg, Max
        
        cutoff_time = timezone.now() - timedelta(hours=time_period_hours)
        
        queryset = DeviceBandwidthUsage.objects.filter(
            device=self.device,
            last_seen__gte=cutoff_time
        )
        
        summary = queryset.aggregate(
            total_bytes_sent=Sum('bytes_sent'),
            total_bytes_received=Sum('bytes_received'),
            total_connections=Count('connections'),
            unique_ips=Count('source_ip', distinct=True),
            avg_bytes_per_ip=Avg('bytes_sent'),
            max_bytes_single_ip=Max('bytes_sent')
        )
        
        # Get top protocols
        protocol_stats = {}
        for usage in queryset:
            for protocol in usage.protocols:
                if protocol not in protocol_stats:
                    protocol_stats[protocol] = 0
                protocol_stats[protocol] += usage.bytes_sent
        
        # Sort protocols by usage
        sorted_protocols = sorted(protocol_stats.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'period_hours': time_period_hours,
            'total_bytes_sent': summary['total_bytes_sent'] or 0,
            'total_bytes_received': summary['total_bytes_received'] or 0,
            'total_bytes_total': (summary['total_bytes_sent'] or 0) + (summary['total_bytes_received'] or 0),
            'total_connections': summary['total_connections'] or 0,
            'unique_ips': summary['unique_ips'] or 0,
            'avg_bytes_per_ip': summary['avg_bytes_per_ip'] or 0,
            'max_bytes_single_ip': summary['max_bytes_single_ip'] or 0,
            'top_protocols': sorted_protocols[:10]  # Top 10 protocols
        }
    
    def get_bandwidth_trends(self, hours=24):
        """Get bandwidth usage trends over time"""
        from datetime import timedelta
        from django.db.models import Sum, Count
        from django.db.models.functions import TruncHour
        
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        # Group by hour
        hourly_data = DeviceBandwidthUsage.objects.filter(
            device=self.device,
            last_seen__gte=cutoff_time
        ).annotate(
            hour=TruncHour('last_seen')
        ).values('hour').annotate(
            bytes_sent=Sum('bytes_sent'),
            bytes_received=Sum('bytes_received'),
            connections=Count('source_ip', distinct=True)
        ).order_by('hour')
        
        trends = []
        for data in hourly_data:
            trends.append({
                'hour': data['hour'],
                'bytes_sent': data['bytes_sent'] or 0,
                'bytes_received': data['bytes_received'] or 0,
                'total_bytes': (data['bytes_sent'] or 0) + (data['bytes_received'] or 0),
                'unique_ips': data['connections']
            })
        
        return trends
