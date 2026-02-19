"""
Automated Server Status Monitoring Service
Provides automatic status updates for all servers in the monitoring system
"""

import logging
import threading
import time
import concurrent.futures
from datetime import datetime, timedelta
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
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait 1 minute on error
    
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
