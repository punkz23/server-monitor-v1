"""
ISP monitoring module for Converge and PLDT connections
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import ping3
import dns.resolver
import requests
from django.utils import timezone

from .models import ISPConnection, ISPMetric, ISPFailover

logger = logging.getLogger(__name__)


class ISPMonitor:
    """ISP connection monitoring for latency, packet loss, DNS, and bandwidth"""
    
    def __init__(self, isp_connection: ISPConnection):
        self.isp = isp_connection
        self.gateway = str(isp_connection.gateway_ip)
        self.dns_servers = [dns.strip() for dns in isp_connection.dns_servers.split(',') if dns.strip()]
    
    def test_latency(self) -> Optional[float]:
        """Test latency to gateway in milliseconds"""
        try:
            response_time = ping3.ping(self.gateway, timeout=2)
            return round(response_time * 1000, 2) if response_time else None  # Convert to ms and round
        except Exception as e:
            logger.error(f"Latency test failed for {self.isp.name}: {e}")
            return None
    
    def test_packet_loss(self) -> float:
        """Test packet loss by sending multiple pings"""
        lost = 0
        total = 5
        
        for _ in range(total):
            try:
                if not ping3.ping(self.gateway, timeout=1):
                    lost += 1
            except Exception:
                lost += 1
        
        return round((lost / total) * 100, 2)  # Round to 2 decimal places
    
    def test_dns_resolution(self) -> bool:
        """Test DNS resolution using ISP's DNS servers"""
        try:
            if not self.dns_servers:
                # Fallback to public DNS
                resolver = dns.resolver.Resolver()
                resolver.resolve('google.com', 'A')
            else:
                resolver = dns.resolver.Resolver()
                resolver.nameservers = self.dns_servers
                resolver.resolve('google.com', 'A')
            return True
        except Exception as e:
            logger.error(f"DNS test failed for {self.isp.name}: {e}")
            return False
    
    def test_bandwidth(self) -> Optional[float]:
        """Test actual bandwidth using real speed tests"""
        try:
            # Always use real speed tests for accurate, dynamic measurements
            logger.info(f"Running real bandwidth test for {self.isp.name}")
            return self._direct_bandwidth_test()
            
        except Exception as e:
            logger.error(f"Bandwidth test failed for {self.isp.name}: {e}")
            return None
    
    def _get_firewall_bandwidth(self) -> Optional[float]:
        """Get bandwidth measurement from Sophos Firewall"""
        try:
            from monitor.services.firewall_interface_monitor import FirewallInterfaceMonitor
            
            # Connect to Sophos Firewall
            firewall = FirewallInterfaceMonitor()
            
            # Get interface statistics
            interfaces = firewall.get_interfaces()
            
            if not interfaces:
                logger.warning("No interface data available from Sophos Firewall")
                return None
            
            # Find the WAN interface based on ISP gateway IP
            wan_interface = self._find_wan_interface(interfaces)
            
            if not wan_interface:
                logger.warning(f"No WAN interface found for ISP {self.isp.name}")
                return None
            
            # Calculate bandwidth from interface usage
            # This is a simplified calculation - in reality, you'd need to measure over time
            interface_usage = wan_interface.get('usage', 0)
            
            # Convert interface usage to estimated bandwidth
            # This is a rough estimation - you may need to calibrate based on your setup
            estimated_bandwidth = self._estimate_bandwidth_from_usage(wan_interface, interface_usage)
            
            logger.info(f"Firewall bandwidth measurement for {self.isp.name}: {estimated_bandwidth:.2f} Mbps")
            return estimated_bandwidth
            
        except Exception as e:
            logger.error(f"Firewall bandwidth measurement failed: {e}")
            return None
    
    def _find_wan_interface(self, interfaces: List[Dict]) -> Optional[Dict]:
        """Find the WAN interface for this ISP based on gateway IP"""
        try:
            isp_gateway = str(self.isp.gateway_ip)
            isp_name = self.isp.name.lower()
            
            logger.info(f"Finding WAN interface for {self.isp.name} (gateway: {isp_gateway})")
            
            # Look for interface that matches the ISP's gateway network
            for interface in interfaces:
                interface_name = interface.get('name', '').lower()
                interface_ip = interface.get('ip_address', '')
                
                logger.debug(f"Checking interface: {interface.get('name')} (IP: {interface_ip})")
                
                # Check if this interface matches the ISP
                if self._is_wan_interface_for_isp(interface_name, interface_ip, isp_gateway):
                    logger.info(f"Selected interface {interface.get('name')} for ISP {self.isp.name}")
                    return interface
            
            # Enhanced fallback: look for interfaces with ISP-specific patterns
            for interface in interfaces:
                interface_name = interface.get('name', '').lower()
                
                if ('pldt' in isp_name and 'pldt' in interface_name) or \
                   ('converge' in isp_name and 'converge' in interface_name) or \
                   ('globe' in isp_name and ('globe' in interface_name or 'prepaid' in interface_name)):
                    logger.warning(f"Using fallback interface {interface.get('name')} for ISP {self.isp.name}")
                    return interface
            
            # Last resort: look for any WAN interface
            for interface in interfaces:
                if 'wan' in interface.get('name', '').lower():
                    logger.warning(f"Using generic WAN interface {interface.get('name')} for ISP {self.isp.name}")
                    return interface
            
            logger.error(f"No WAN interface found for ISP {self.isp.name}")
            return None
            
        except Exception as e:
            logger.error(f"Error finding WAN interface: {e}")
            return None
    
    def _is_wan_interface_for_isp(self, interface_name: str, interface_ip: str, isp_gateway: str) -> bool:
        """Check if an interface belongs to the ISP's WAN connection"""
        try:
            isp_name = self.isp.name.lower()
            interface_name_lower = interface_name.lower()
            
            # Primary matching based on ISP name patterns in interface names
            if 'pldt' in isp_name and ('pldt' in interface_name_lower or 'wan' in interface_name_lower):
                return True
            elif 'converge' in isp_name and 'converge' in interface_name_lower:
                return True
            elif 'globe' in isp_name and ('globe' in interface_name_lower or 'prepaid' in interface_name_lower):
                return True
            elif 'smart' in isp_name and ('smart' in interface_name_lower):
                return True
            
            # Fallback: for generic WAN interfaces, try network matching (less reliable)
            elif 'wan' in interface_name_lower and interface_ip and isp_gateway:
                return self._ip_in_same_network(interface_ip, isp_gateway)
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking WAN interface for ISP: {e}")
            return False
    
    def _ip_in_same_network(self, ip1: str, ip2: str) -> bool:
        """Check if two IPs are in the same /24 network"""
        try:
            import ipaddress
            net1 = ipaddress.IPv4Network(f"{ip1}/24", strict=False)
            net2 = ipaddress.IPv4Network(f"{ip2}/24", strict=False)
            return net1.network_address == net2.network_address
        except Exception:
            return False
    
    def _estimate_bandwidth_from_usage(self, interface: Dict, usage: int) -> float:
        """Estimate bandwidth using hybrid approach: subscription speed + usage-based adjustment"""
        try:
            interface_name = interface.get('name', '').lower()
            
            # Get ISP subscription speed
            max_bandwidth = self._get_isp_subscription_speed()
            
            # Base bandwidth estimation using hybrid approach
            if 'wan' in interface_name or 'pldt' in interface_name or 'converge' in interface_name:
                # Hybrid calculation: Start with subscription speed, adjust based on usage
                estimated_bandwidth = self._calculate_hybrid_bandwidth(usage, max_bandwidth)
                return estimated_bandwidth
            else:
                # For other interfaces, use a simpler calculation
                return max(usage * 0.1, 0.5)
                
        except Exception as e:
            logger.error(f"Error estimating bandwidth: {e}")
            return 1.0  # Default fallback
    
    def _calculate_hybrid_bandwidth(self, usage: int, subscription_speed: float) -> float:
        """Calculate bandwidth using hybrid approach: subscription + usage adjustment"""
        try:
            # Usage percentage (0-100 scale)
            usage_percentage = min(usage / 100.0, 1.0)  # Normalize usage to 0-1 scale
            
            # Base bandwidth from subscription speed
            base_bandwidth = subscription_speed * 0.7  # Start at 70% of subscription
            
            # Usage-based adjustment factor
            if usage_percentage >= 0.8:  # High usage (80%+)
                adjustment_factor = 1.2  # Boost by 20%
            elif usage_percentage >= 0.5:  # Medium usage (50%+)
                adjustment_factor = 1.0  # No adjustment
            elif usage_percentage >= 0.2:  # Low usage (20%+)
                adjustment_factor = 0.8  # Reduce by 20%
            else:  # Very low usage (<20%)
                adjustment_factor = 0.6  # Reduce by 40%
            
            # Calculate final bandwidth
            estimated_bandwidth = base_bandwidth * adjustment_factor
            
            # Ensure bandwidth is within reasonable bounds
            min_bandwidth = subscription_speed * 0.1  # Minimum 10% of subscription
            max_bandwidth = subscription_speed * 0.95   # Maximum 95% of subscription
            
            final_bandwidth = max(min_bandwidth, min(estimated_bandwidth, max_bandwidth))
            
            logger.info(f"Hybrid bandwidth: usage={usage}, subscription={subscription_speed}Mbps, "
                       f"factor={adjustment_factor}, result={final_bandwidth:.2f}Mbps")
            
            return round(final_bandwidth, 2)
            
        except Exception as e:
            logger.error(f"Error calculating hybrid bandwidth: {e}")
            return subscription_speed * 0.5  # Fallback to 50% of subscription
    
    def _get_isp_subscription_speed(self) -> float:
        """Get the actual subscription speed for this ISP"""
        try:
            isp_name = self.isp.name.lower()
            
            # Known ISP subscription speeds
            if 'pldt' in isp_name:
                return 300.0  # PLDT 300 Mbps
            elif 'converge' in isp_name:
                return 100.0  # Converge 100 Mbps
            elif 'globe' in isp_name:
                return 50.0   # Globe 50 Mbps (typical)
            elif 'smart' in isp_name:
                return 50.0   # Smart 50 Mbps (typical)
            else:
                # Default to 100 Mbps for unknown ISPs
                logger.warning(f"Unknown ISP {self.isp.name}, using default 100 Mbps")
                return 100.0
                
        except Exception as e:
            logger.error(f"Error getting ISP subscription speed: {e}")
            return 100.0  # Default fallback
    
    def _direct_bandwidth_test(self) -> Optional[float]:
        """Fallback direct bandwidth test (original method)"""
        try:
            # Use the original direct internet testing method
            test_urls = [
                'https://speed.cloudflare.com/__down?bytes=52428800',  # 50MB
                'https://proof.ovh.net/files/100Mb.dat',
                'http://speedtest.tele2.net/100MB.zip'
            ]
            
            best_bandwidth = 0
            for test_url in test_urls:
                try:
                    response = requests.get(test_url, timeout=30, stream=True)
                    start_time = datetime.now()
                    downloaded = 0
                    
                    # Test for exactly 10 seconds
                    test_duration = 10
                    
                    for chunk in response.iter_content(chunk_size=32768):
                        downloaded += len(chunk)
                        elapsed = (datetime.now() - start_time).total_seconds()
                        
                        if elapsed >= test_duration:
                            break
                    
                    duration = (datetime.now() - start_time).total_seconds()
                    
                    if duration >= 8 and downloaded > 0:
                        bandwidth_mbps = (downloaded * 8) / (duration * 1024 * 1024)
                        logger.info(f"Direct bandwidth test from {test_url}: {bandwidth_mbps:.2f} Mbps")
                        best_bandwidth = max(best_bandwidth, bandwidth_mbps)
                        
                except Exception as e:
                    logger.warning(f"Direct bandwidth test failed for {test_url}: {e}")
                    continue
            
            if best_bandwidth > 0:
                return round(best_bandwidth * 0.95, 2)  # Apply overhead correction
            return None
            
        except Exception as e:
            logger.error(f"Direct bandwidth test failed for {self.isp.name}: {e}")
            return None
    
    def _simple_bandwidth_test(self) -> Optional[float]:
        """Fallback simple bandwidth test using smaller files"""
        try:
            # Try a more reliable approach with multiple concurrent downloads
            import threading
            import queue
            
            test_urls = [
                'https://httpbin.org/bytes/1048576',  # 1MB
                'https://httpbin.org/bytes/2097152',  # 2MB
                'https://httpbin.org/bytes/5242880',  # 5MB
            ]
            
            results = queue.Queue()
            
            def download_test(url, thread_id):
                try:
                    start_time = datetime.now()
                    response = requests.get(url, timeout=15)
                    
                    if response.status_code == 200:
                        downloaded = len(response.content)
                        duration = (datetime.now() - start_time).total_seconds()
                        
                        if duration > 0.5:  # Minimum 0.5 seconds
                            bandwidth_mbps = (downloaded * 8) / (duration * 1024 * 1024)
                            results.put(bandwidth_mbps)
                            logger.info(f"Thread {thread_id} test from {url}: {bandwidth_mbps:.2f} Mbps")
                            
                except Exception as e:
                    logger.warning(f"Thread {thread_id} bandwidth test failed for {url}: {e}")
            
            # Run multiple downloads concurrently
            threads = []
            for i, url in enumerate(test_urls[:3]):  # Use up to 3 concurrent downloads
                thread = threading.Thread(target=download_test, args=(url, i))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join(timeout=20)
            
            # Collect results
            bandwidths = []
            while not results.empty():
                try:
                    bandwidths.append(results.get_nowait())
                except queue.Empty:
                    break
            
            if bandwidths:
                # Use the median to avoid outliers
                bandwidths.sort()
                median_bandwidth = bandwidths[len(bandwidths) // 2]
                return round(median_bandwidth, 2)
            
            return None
        except Exception as e:
            logger.error(f"Simple bandwidth test failed for {self.isp.name}: {e}")
            return None
    
    def test_internet_connectivity(self) -> bool:
        """Test if ISP can reach internet via HTTP"""
        try:
            # Use multiple reliable endpoints for better connectivity testing
            test_endpoints = [
                'https://httpbin.org/status/200',
                'https://api.ipify.org',  # Simple IP check
                'https://google.com',  # Basic connectivity test
                'https://cloudflare.com',  # CDN reliability
                'https://1.1.1.1/'  # Basic DNS resolver test
            ]
            
            success_count = 0
            for endpoint in test_endpoints:
                try:
                    if '1.1.1.1' in endpoint:
                        # Special handling for DNS resolver
                        import socket
                        socket.gethostbyname('1.1.1.1')
                        success_count += 1
                    else:
                        response = requests.get(endpoint, timeout=3)
                        if response.status_code == 200:
                            success_count += 1
                            logger.info(f"Connectivity test passed for {self.isp.name}: {endpoint}")
                        else:
                            logger.warning(f"Connectivity test failed for {self.isp.name}: {endpoint} - Status {response.status_code}")
                except Exception as e:
                    logger.warning(f"Connectivity test error for {self.isp.name} - {endpoint}: {e}")
                    continue
            
            # Consider internet up if at least 2 endpoints succeed
            is_connected = success_count >= 2
            logger.info(f"Internet connectivity for {self.isp.name}: {success_count}/{len(test_endpoints)} endpoints successful, status: {'UP' if is_connected else 'DOWN'}")
            
            return is_connected
            
        except Exception as e:
            logger.error(f"Internet connectivity test failed for {self.isp.name}: {e}")
            return False
    
    def test_jitter(self) -> Optional[float]:
        """Test network jitter (variation in latency)"""
        latencies = []
        
        for _ in range(5):
            latency = self.test_latency()
            if latency:
                latencies.append(latency)
        
        if len(latencies) < 2:
            return None
        
        # Calculate standard deviation
        avg_latency = sum(latencies) / len(latencies)
        variance = sum((lat - avg_latency) ** 2 for lat in latencies) / len(latencies)
        jitter = variance ** 0.5
        
        return round(jitter, 2)  # Round to 2 decimal places
    
    def check_failover_conditions(self, metrics: Dict) -> bool:
        """Check if failover should be triggered based on metrics"""
        latency = metrics.get('latency_ms', {}).get('value')
        packet_loss = metrics.get('packet_loss_percent', {}).get('value')
        internet_status = metrics.get('internet_status', {}).get('value')
        
        # Failover conditions
        if internet_status == 0:
            return True
        elif packet_loss > 20:  # High packet loss
            return True
        elif latency and latency > 500:  # Very high latency
            return True
        
        return False
    
    def record_failover(self, reason: str, backup_isp: Optional[ISPConnection] = None):
        """Record a failover event"""
        try:
            failover = ISPFailover.objects.create(
                primary_isp=self.isp,
                backup_isp=backup_isp,
                failover_time=timezone.now(),
                reason=reason
            )
            logger.warning(f"Failover recorded for {self.isp.name}: {reason}")
            return failover
        except Exception as e:
            logger.error(f"Failed to record failover for {self.isp.name}: {e}")
            return None
    
    def update_metrics(self) -> Dict[str, Tuple[float, str]]:
        """Collect and store all ISP metrics"""
        if not self.isp.enabled:
            return {}
        
        metrics = {}
        
        # Test latency
        latency = self.test_latency()
        if latency:
            metrics['latency_ms'] = (latency, 'ms')
        
        # Test packet loss
        packet_loss = self.test_packet_loss()
        metrics['packet_loss_percent'] = (packet_loss, '%')
        
        # Test jitter
        jitter = self.test_jitter()
        if jitter:
            metrics['jitter_ms'] = (jitter, 'ms')
        
        # Test DNS
        dns_ok = self.test_dns_resolution()
        metrics['dns_status'] = (1 if dns_ok else 0, 'boolean')
        
        # Test bandwidth
        bandwidth = self.test_bandwidth()
        if bandwidth:
            metrics['bandwidth_mbps'] = (bandwidth, 'Mbps')
        
        # Test internet connectivity
        internet_ok = self.test_internet_connectivity()
        metrics['internet_status'] = (1 if internet_ok else 0, 'boolean')
        
        # Store metrics in database
        for metric_name, (value, unit) in metrics.items():
            ISPMetric.objects.create(
                connection=self.isp,
                metric_name=metric_name,
                value=value,
                unit=unit
            )
        
        # Update last checked timestamp
        self.isp.last_checked = timezone.now()
        self.isp.save(update_fields=['last_checked'])
        
        # Check for failover conditions
        # Convert metrics from tuple format to dict format for failover checking
        metrics_dict_for_failover = {}
        for metric_name, (value, unit) in metrics.items():
            metrics_dict_for_failover[metric_name] = {'value': value, 'unit': unit}
        
        if self.check_failover_conditions(metrics_dict_for_failover):
            self.record_failover(f"Metrics threshold exceeded: {metrics}")
        
        logger.info(f"Updated {len(metrics)} metrics for {self.isp.name}")
        return metrics
    
    def get_status_summary(self) -> Dict:
        """Get current status summary for the ISP connection"""
        latest_metrics = ISPMetric.objects.filter(
            connection=self.isp
        ).order_by("-timestamp")[:10]
        
        metrics_dict = {}
        for metric in latest_metrics:
            if metric.metric_name not in metrics_dict:
                metrics_dict[metric.metric_name] = {
                    'value': metric.value,
                    'unit': metric.unit,
                    'timestamp': metric.timestamp,
                }
        
        # Calculate overall status
        status = self._calculate_status(metrics_dict)
        
        return {
            'status': status,
            'metrics': metrics_dict,
            'last_checked': self.isp.last_checked,
        }
    
    def _calculate_status(self, metrics: Dict) -> str:
        """Calculate ISP status based on metrics"""
        if not metrics:
            return "unknown"
        
        latency = metrics.get('latency_ms', {}).get('value')
        packet_loss = metrics.get('packet_loss_percent', {}).get('value')
        internet_status = metrics.get('internet_status', {}).get('value')
        dns_status = metrics.get('dns_status', {}).get('value')
        
        # Priority-based status calculation
        if internet_status == 0:
            return "critical"
        elif dns_status == 0:
            return "critical"
        elif packet_loss > 20:
            return "critical"
        elif packet_loss > 10 or (latency and latency > 200):
            return "degraded"
        elif packet_loss > 5 or (latency and latency > 100):
            return "warning"
        else:
            return "healthy"


def monitor_all_isps():
    """Monitor all enabled ISP connections"""
    connections = ISPConnection.objects.filter(enabled=True)
    results = {}
    
    for connection in connections:
        try:
            monitor = ISPMonitor(connection)
            metrics = monitor.update_metrics()
            results[connection.name] = {
                'success': True,
                'metrics_count': len(metrics),
                'status': monitor.get_status_summary()['status']
            }
        except Exception as e:
            logger.error(f"Failed to monitor {connection.name}: {e}")
            results[connection.name] = {
                'success': False,
                'error': str(e)
            }
    
    return results


def get_isp_health_score():
    """Calculate overall ISP health score (0-100)"""
    connections = ISPConnection.objects.filter(enabled=True)
    if not connections:
        return 0
    
    total_score = 0
    for connection in connections:
        monitor = ISPMonitor(connection)
        summary = monitor.get_status_summary()
        
        # Score based on status
        status_scores = {
            'healthy': 100,
            'warning': 75,
            'degraded': 50,
            'critical': 25,
            'unknown': 0
        }
        
        total_score += status_scores.get(summary['status'], 0)
    
    return total_score // len(connections)


def get_individual_isp_health_score(isp_connection):
    """Calculate health score for a specific ISP connection (0-100)"""
    monitor = ISPMonitor(isp_connection)
    summary = monitor.get_status_summary()
    
    # Score based on status
    status_scores = {
        'healthy': 100,
        'warning': 75,
        'degraded': 50,
        'critical': 25,
        'unknown': 0
    }
    
    return status_scores.get(summary['status'], 0)
