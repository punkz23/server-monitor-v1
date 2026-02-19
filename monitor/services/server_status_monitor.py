"""
Automated Server Status Monitoring Service
Provides automatic status updates for all servers in the monitoring system
"""

import logging
import threading
import time
import concurrent.futures
from datetime import datetime, timedelta, timezone as dt_timezone
from django.utils import timezone
from monitor.models import Server
import requests
import socket
import subprocess
import os

logger = logging.getLogger(__name__)


class ServerStatusMonitor:
    """Automated server status monitoring service"""
    
    def __init__(self, check_interval=300):  # 5 minutes default
        self.check_interval = check_interval
        self.running = False
        self.thread = None
        from monitor.services.notification_service import NotificationService
        self.notifications = NotificationService()
    
    def start(self):
        """Start the automated monitoring"""
        if self.running:
            logger.warning("Server status monitor is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info(f"Server status monitor started (interval: {self.check_interval}s)")
    
    def stop(self):
        """Stop the automated monitoring"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=10)
        logger.info("Server status monitor stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                self.update_all_server_status()
                # Also update performance metrics
                self.update_all_server_metrics()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait 1 minute on error
    
    def update_all_server_metrics(self):
        """Update performance metrics for all enabled servers with SSH credentials"""
        from django.core.cache import cache
        from monitor.models_ssh_credentials import SSHCredential
        
        # Get servers that have active SSH credentials
        # The related name in monitor/models_ssh_credentials.py is 'ssh_credential'
        servers = list(Server.objects.filter(
            enabled=True, 
            ssh_credential__isnull=False,
            ssh_credential__is_active=True
        ))
        
        if not servers:
            return
            
        logger.info(f"Starting metrics update for {len(servers)} servers")
        
        server_metrics = {}
        
        # Use ThreadPoolExecutor for concurrent metrics collection
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_server = {
                executor.submit(self.monitor_server_metrics, server): server 
                for server in servers
            }
            
            for future in concurrent.futures.as_completed(future_to_server):
                server = future_to_server[future]
                try:
                    metrics = future.result()
                    if metrics:
                        server_metrics[server.id] = metrics
                except Exception as e:
                    logger.error(f"Error monitoring metrics for {server.name}: {e}")
        
        # Update cache for dashboard
        if server_metrics:
            cache.set("dashboard_metrics", server_metrics, 600) # 10 min cache

    def evaluate_ssl_alerts(self, server, ssl_cert):
        """Evaluate SSL certificate expiration and create alerts if needed"""
        from monitor.models import AlertEvent, AlertRule
        
        days = ssl_cert.days_until_expiry
        if days is None:
            return

        severity = None
        message = ""
        
        if days < 0:
            severity = AlertRule.SEVERITY_CRIT
            message = f"SSL Certificate for {ssl_cert.domain} has EXPIRED ({abs(days)} days ago)."
        elif days <= ssl_cert.critical_days:
            severity = AlertRule.SEVERITY_CRIT
            message = f"SSL Certificate for {ssl_cert.domain} expires in {days} days (CRITICAL)."
        elif days <= ssl_cert.warning_days:
            severity = AlertRule.SEVERITY_WARN
            message = f"SSL Certificate for {ssl_cert.domain} expires in {days} days (Warning)."
        
        if severity:
            # Check if alert already exists for this domain recently
            recent_alert = AlertEvent.objects.filter(
                server=server,
                title__contains=ssl_cert.domain,
                is_recovery=False,
                created_at__gte=timezone.now() - timedelta(hours=24)
            ).exists()
            
            if not recent_alert:
                AlertEvent.objects.create(
                    server=server,
                    kind="ssl_expiry",
                    severity=severity,
                    title=f"SSL Expiry: {ssl_cert.domain}",
                    message=message,
                    value=float(days)
                )
                # Send Push Notification
                self.notifications.send_notification(['push'], 'admin', f"SSL Expiry: {ssl_cert.domain}", message)
        else:
            # Check if we should create a recovery alert
            was_in_alert = AlertEvent.objects.filter(
                server=server,
                title__contains=ssl_cert.domain,
                is_recovery=False,
                created_at__gte=timezone.now() - timedelta(days=7)
            ).exists()
            
            if was_in_alert:
                # Create recovery event
                recovery_msg = f"SSL Certificate for {ssl_cert.domain} is now valid ({days} days remaining)."
                AlertEvent.objects.create(
                    server=server,
                    kind="ssl_expiry",
                    severity=AlertRule.SEVERITY_INFO,
                    title=f"SSL Recovery: {ssl_cert.domain}",
                    message=recovery_msg,
                    value=float(days),
                    is_recovery=True
                )
                # Send Push Notification
                self.notifications.send_notification(['push'], 'admin', f"SSL Recovery: {ssl_cert.domain}", recovery_msg)

    def monitor_server_metrics(self, server):
        """Collect and save metrics for a single server"""
        from monitor.services.metrics_monitor_service import MetricsMonitorService
        from monitor.models import ResourceSample
        
        try:
            # Check if server is up first to avoid SSH timeouts
            if server.last_status != Server.STATUS_UP:
                return
                
            monitor = MetricsMonitorService()
            metrics_data = monitor.get_comprehensive_metrics(server.ip_address, server=server)
            
            if 'error' not in metrics_data and 'current' in metrics_data:
                current = metrics_data['current']
                cpu = current.get('cpu', {})
                ram = current.get('ram', {})
                system = current.get('system', {})
                
                # Save to ResourceSample for performance trends
                ResourceSample.objects.create(
                    server=server,
                    collected_at=timezone.now(),
                    cpu_percent=cpu.get('usage_percent'),
                    ram_percent=ram.get('usage_percent'),
                    uptime_seconds=system.get('uptime_seconds')
                )
                
                # Update SSL certificates in database
                ssl_list = current.get('ssl', [])
                if ssl_list:
                    from monitor.models import SSLCertificate
                    for ssl_item in ssl_list:
                        try:
                            # Parse expiration date
                            expires_at = None
                            if ssl_item.get('expiry_date'):
                                try:
                                    expires_at = datetime.strptime(ssl_item['expiry_date'], '%Y-%m-%d').replace(tzinfo=dt_timezone.utc)
                                except ValueError:
                                    pass
                            
                            # Update or create certificate record
                            ssl_obj, created = SSLCertificate.objects.update_or_create(
                                server=server,
                                domain=ssl_item.get('hostname'),
                                defaults={
                                    'name': ssl_item.get('common_name', server.name),
                                    'issuer': ssl_item.get('issuer'),
                                    'expires_at': expires_at,
                                    'days_until_expiry': ssl_item.get('days_remaining'),
                                    'is_valid': ssl_item.get('status') != 'expired',
                                    'last_checked': timezone.now(),
                                    'enabled': True
                                }
                            )

                            # Evaluate SSL alerts
                            self.evaluate_ssl_alerts(server, ssl_obj)
                        except Exception as ssl_err:
                            logger.error(f"Error saving SSL cert for {server.name}: {ssl_err}")

                # Update server fields for real-time display
                server.last_resource_checked = timezone.now()
                server.last_cpu_percent = cpu.get('usage_percent')
                server.last_ram_percent = ram.get('usage_percent')
                server.last_uptime_seconds = system.get('uptime_seconds')
                server.save(update_fields=[
                    'last_resource_checked', 'last_cpu_percent', 
                    'last_ram_percent', 'last_uptime_seconds'
                ])
                
                return current
            return None
        except Exception as e:
            logger.error(f"Failed to monitor metrics for {server.name}: {e}")
            return None

    def update_all_server_status(self):
        """Update status for all enabled servers"""
        servers = list(Server.objects.filter(enabled=True))
        updated_count = 0
        up_count = 0
        down_count = 0
        
        logger.info(f"Starting status update for {len(servers)} servers")
        
        # Use ThreadPoolExecutor for concurrent checks
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            # Map future to server
            future_to_server = {
                executor.submit(self.check_server_status, server): server 
                for server in servers
            }
            
            for future in concurrent.futures.as_completed(future_to_server):
                server = future_to_server[future]
                try:
                    # Unpack the result tuple
                    is_up, method = future.result()
                    
                    # Update server status
                    old_status = server.last_status
                    if is_up:
                        server.last_status = Server.STATUS_UP
                        up_count += 1
                        if old_status != Server.STATUS_UP:
                            logger.info(f"Server {server.name} ({server.ip_address}) is now UP (Method: {method})")
                    else:
                        server.last_status = Server.STATUS_DOWN
                        down_count += 1
                        if old_status != Server.STATUS_DOWN:
                            logger.warning(f"Server {server.name} ({server.ip_address}) is now DOWN")
                    
                    server.last_checked = timezone.now()
                    server.save()
                    updated_count += 1
                    
                except Exception as e:
                    logger.error(f"Error checking server {server.name}: {e}")
        
        uptime_percentage = round((up_count / updated_count * 100) if updated_count > 0 else 0, 1)
        logger.info(f"Status update completed: {up_count} up, {down_count} down, {uptime_percentage}% uptime")
        
        return {
            'updated': updated_count,
            'up': up_count,
            'down': down_count,
            'uptime_percentage': uptime_percentage
        }
    
    def check_server_status(self, server, timeout=5):
        """Check if server is up using multiple methods - prioritizing service checks"""
        ip_address = server.ip_address
        
        # Determine SSL verification behavior
        verify_ssl = not server.skip_ssl_verification

        # Prioritize HTTPS if configured for the server, otherwise HTTP
        if server.use_https:
            # Method 1: HTTPS request with verification (if enabled)
            try:
                requests.get(f'https://{ip_address}', timeout=timeout, verify=verify_ssl)
                return True, "HTTPS"
            except requests.exceptions.RequestException:
                pass
            
            # If verification failed but skip_ssl_verification is true, try without it
            if not verify_ssl:
                try:
                    requests.get(f'https://{ip_address}', timeout=timeout, verify=False)
                    return True, "HTTPS (unverified)"
                except requests.exceptions.RequestException:
                    pass

        # Method 2: HTTP request (if not primarily HTTPS or if HTTPS failed)
        try:
            requests.get(f'http://{ip_address}', timeout=timeout)
            return True, "HTTP"
        except requests.exceptions.RequestException:
            pass

        # Method 2.5: Check the explicitly configured port
        if server.port and server.port not in [80, 443]:
            try:
                with socket.create_connection((ip_address, server.port), timeout=timeout):
                    return True, f"TCP:{server.port}"
            except (socket.error, socket.timeout):
                pass

        # Method 3: Port check (HTTPS) - regardless of use_https setting, try if it's open
        try:
            with socket.create_connection((ip_address, 443), timeout=timeout):
                return True, "TCP:443"
        except (socket.error, socket.timeout):
            pass

        # Method 4: Port check (HTTP) - regardless of use_https setting, try if it's open
        try:
            with socket.create_connection((ip_address, 80), timeout=timeout):
                return True, "TCP:80"
        except (socket.error, socket.timeout):
            pass

        # Method 5: Check common NAS ports (for Synology, QNAP, etc.)
        nas_ports = [5001, 5000, 8080, 8443, 22, 21, 445]  # Synology DSM, web UI, SSH, FTP, SMB
        for port in nas_ports:
            try:
                with socket.create_connection((ip_address, port), timeout=timeout):
                    return True, f"TCP:{port}"
            except (socket.error, socket.timeout):
                continue

        # Method 6: Ping (LAST RESORT - less reliable)
        try:
            if os.name == 'nt':  # Windows
                result = subprocess.run(['ping', '-n', '1', ip_address], 
                                      capture_output=True, text=True, timeout=timeout)
            else:  # Linux/Mac
                result = subprocess.run(['ping', '-c', '1', ip_address], 
                                      capture_output=True, text=True, timeout=timeout)
            
            if result.returncode == 0:
                # Ping succeeded but all services failed - this is likely a false positive
                return False, "Ping (False Positive)"
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass

        return False, "None"
    
    def update_single_server(self, ip_address):
        """Update status for a single server"""
        try:
            server = Server.objects.get(ip_address=ip_address, enabled=True)
            is_up, method = self.check_server_status(server)
            old_status = server.last_status
            
            if is_up:
                server.last_status = Server.STATUS_UP
                if old_status != Server.STATUS_UP:
                    logger.info(f"Server {server.name} ({server.ip_address}) is now UP (Method: {method})")
            else:
                server.last_status = Server.STATUS_DOWN
                if old_status != Server.STATUS_DOWN:
                    logger.warning(f"Server {server.name} ({server.ip_address}) is now DOWN")
            
            server.last_checked = timezone.now()
            server.save()
            
            return {
                'server': server.name,
                'ip_address': server.ip_address,
                'old_status': old_status,
                'new_status': server.last_status,
                'is_up': is_up,
                'method': method
            }
            
        except Server.DoesNotExist:
            logger.error(f"Server with IP {ip_address} not found")
            return None
        except Exception as e:
            logger.error(f"Error updating server {ip_address}: {e}")
            return None


# Global monitor instance
_monitor_instance = None

def get_server_monitor():
    """Get or create the global server monitor instance"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = ServerStatusMonitor()
    return _monitor_instance

def start_automated_monitoring():
    """Start automated server status monitoring"""
    monitor = get_server_monitor()
    monitor.start()
    return monitor

def stop_automated_monitoring():
    """Stop automated server status monitoring"""
    monitor = get_server_monitor()
    monitor.stop()
    return monitor
