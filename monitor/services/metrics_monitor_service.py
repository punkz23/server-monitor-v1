"""
Comprehensive Metrics Monitoring Service
Monitors CPU, RAM, Disk usage and SSL certificate expiration with change tracking
"""

import logging
import paramiko
import json
import re
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache

logger = logging.getLogger(__name__)


class MetricsMonitorService:
    """Advanced metrics monitoring with change detection"""
    
    def __init__(self):
        # SSH credentials will be loaded from database dynamically
        self.ssh_credentials = {}
    
    def load_ssh_credentials(self, ip_address: str = None):
        """Load SSH credentials from database"""
        try:
            from monitor.models_ssh_credentials import SSHCredential
            
            if ip_address:
                # Load credentials for specific IP
                credential = SSHCredential.objects.filter(
                    server__ip_address=ip_address, 
                    is_active=True
                ).first()
                if credential:
                    self.ssh_credentials[ip_address] = {
                        'username': credential.username,
                        'password': credential.get_password(),
                        'port': credential.port
                    }
            else:
                # Load all active credentials
                credentials = SSHCredential.objects.filter(is_active=True).select_related('server')
                for cred in credentials:
                    self.ssh_credentials[cred.server.ip_address] = {
                        'username': cred.username,
                        'password': cred.get_password(),
                        'port': cred.port
                    }
                    
        except Exception as e:
            logger.error(f"Error loading SSH credentials: {e}")
    
    def get_comprehensive_metrics(self, ip_address: str, server=None) -> dict:
        """Get all metrics for a device with change tracking"""
        try:
            # 1. Try agent-sourced metrics first if server object is provided
            if server:
                try:
                    from monitor.models_metrics import ServerMetrics
                    # Look for the most recent metrics from this server
                    recent_agent_metrics = ServerMetrics.objects.filter(
                        server=server
                    ).order_by('-timestamp').first()
                    
                    # If we have agent metrics and they are recent (less than 10 minutes old)
                    if recent_agent_metrics and (timezone.now() - recent_agent_metrics.timestamp).total_seconds() < 600:
                        current_metrics = self.format_agent_metrics(recent_agent_metrics, server)
                        
                        # Detect changes against cache
                        cached_data = self.get_cached_metrics(ip_address)
                        cached_metrics = cached_data.get('metrics', {}) if cached_data else {}
                        changes = {}
                        if cached_metrics:
                            changes = self.detect_changes(cached_metrics, current_metrics)
                        
                        # Update cache with new metrics
                        self.update_metrics_cache(ip_address, current_metrics, changes)
                        
                        return {
                            'current': current_metrics,
                            'changes': changes,
                            'timestamp': recent_agent_metrics.timestamp.isoformat(),
                            'cached': False,
                            'source': 'agent'
                        }
                except Exception as e:
                    logger.warning(f"Error retrieving agent metrics for {ip_address}: {e}")

            # 2. Fallback to legacy polling/cache logic
            # Get cached metrics first
            cached_data = self.get_cached_metrics(ip_address)
            if cached_data:
                cached_metrics = cached_data.get('metrics', {})
                current_metrics = self.collect_current_metrics(ip_address, server=server)
                changes = self.detect_changes(cached_metrics, current_metrics)
                
                # Update cache with new metrics
                self.update_metrics_cache(ip_address, current_metrics, changes)
                
                return {
                    'current': current_metrics,
                    'changes': changes,
                    'timestamp': timezone.now().isoformat(),
                    'cached': False
                }
            
            # No cache - collect fresh metrics
            current_metrics = self.collect_current_metrics(ip_address, server=server)
            self.update_metrics_cache(ip_address, current_metrics, {})
            
            return {
                'current': current_metrics,
                'changes': {},
                'timestamp': timezone.now().isoformat(),
                'cached': False
            }
            
        except Exception as e:
            logger.error(f"Error getting metrics for {ip_address}: {e}")
            return {'error': str(e), 'timestamp': timezone.now().isoformat()}

    def format_agent_metrics(self, agent_metrics, server=None) -> dict:
        """Format ServerMetrics model instance into the dictionary format used by the service"""
        metrics = {}
        
        # CPU
        if agent_metrics.cpu_percent is not None:
            cpu_val = agent_metrics.cpu_percent
            metrics['cpu'] = {
                'usage_percent': cpu_val,
                'status': 'normal' if cpu_val < 80 else 'high' if cpu_val < 95 else 'critical',
                'status_color': '#28a745' if cpu_val < 80 else '#ffc107' if cpu_val < 95 else '#dc3545',
                'cores': agent_metrics.cpu_count,
                'load_1m': agent_metrics.load_1m
            }
            
        # RAM
        if agent_metrics.memory_percent is not None:
            ram_val = agent_metrics.memory_percent
            metrics['ram'] = {
                'usage_percent': ram_val,
                'status': 'normal' if ram_val < 80 else 'high' if ram_val < 95 else 'critical',
                'status_color': '#28a745' if ram_val < 80 else '#ffc107' if ram_val < 95 else '#dc3545',
                'total_gb': agent_metrics.memory_gb,
                'used_gb': agent_metrics.memory_used_gb
            }
            
        # Disk
        if agent_metrics.disk_percent is not None:
            disk_val = agent_metrics.disk_percent
            metrics['disk'] = {
                'usage_percent': disk_val,
                'status': 'normal' if disk_val < 80 else 'high' if disk_val < 95 else 'critical',
                'status_color': '#28a745' if disk_val < 80 else '#ffc107' if disk_val < 95 else '#dc3545',
                'total_gb': agent_metrics.disk_gb,
                'used_gb': agent_metrics.disk_used_gb
            }
            
        # System
        metrics['system'] = {
            'uptime_seconds': agent_metrics.uptime_seconds,
            'uptime_days': agent_metrics.uptime_days,
            'process_count': agent_metrics.process_count,
            'hostname': agent_metrics.hostname
        }
        
        # SSL and Directory Watch still need SSH for now as agent might not report them yet
        # or we could try to collect them if available. 
        # For now, we'll just return what the agent gave us.
        
        # Directory metrics
        if agent_metrics.directory_metrics:
            formatted_dirs = []
            for d in agent_metrics.directory_metrics:
                # Ensure timestamp is ISO formatted or None
                if d.get('newest_folder_last_modified') and isinstance(d['newest_folder_last_modified'], (int, float)):
                    d['newest_folder_last_modified'] = datetime.fromtimestamp(d['newest_folder_last_modified']).isoformat()
                formatted_dirs.append(d)
            metrics['directory_watch'] = formatted_dirs
        else:
            metrics['directory_watch'] = [] # Ensure it's always an array

        # SSL metrics
        ssl_metrics = getattr(agent_metrics, 'ssl_metrics', [])
        if ssl_metrics:
            metrics['ssl'] = ssl_metrics
        else:
            metrics['ssl'] = [] # Ensure it's always an array
        
        return metrics

    def get_server_metrics(self, server) -> dict:
        """Get metrics for a specific server instance"""
        return self.get_comprehensive_metrics(server.ip_address, server=server)

    def collect_current_metrics(self, ip_address: str, server=None) -> dict:
        """Collect current metrics from device"""
        metrics = {}
        
        # Load SSH credentials for this IP
        self.load_ssh_credentials(ip_address)
        
        # Check if credentials exist
        if ip_address not in self.ssh_credentials:
            return {'error': f'No SSH credentials configured for {ip_address}'}
        
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            creds = self.ssh_credentials.get(ip_address, {})
            ssh.connect(
                hostname=ip_address,
                username=creds.get('username', ''),
                password=creds.get('password', ''),
                port=creds.get('port', 22),
                timeout=10,
                allow_agent=False,
                look_for_keys=False
            )
            
            # CPU Usage
            cpu_usage = self.get_cpu_usage(ssh)
            if cpu_usage:
                metrics['cpu'] = cpu_usage
            
            # RAM Usage
            ram_usage = self.get_ram_usage(ssh)
            if ram_usage:
                metrics['ram'] = ram_usage
            
            # Disk Usage
            disk_usage = self.get_disk_usage(ssh)
            if disk_usage:
                metrics['disk'] = disk_usage
            
            # SSL Certificate Expiration
            logger.info(f"Checking SSL for {ip_address}, server type: {server.server_type if server else 'None'}")
            ssl_info = self.get_ssl_expiration(ssh, ip_address, server)
            if ssl_info:
                metrics['ssl'] = ssl_info
                logger.info(f"SSL certificates found for {ip_address}: {len(ssl_info)}")
            else:
                logger.info(f"No SSL certificates found for {ip_address}")
            
            # Directory Watch (Using server's monitored_directories)
            if server:
                dir_paths = [p.strip() for p in server.monitored_directories.split(',') if p.strip()]
                logger.info(f"Server {server.name} monitored directories: {dir_paths}")
            else:
                dir_paths = ['/var/www/html', '/home/user/logs']
                logger.info(f"Using default directories: {dir_paths}")
                
            dir_status = self.get_directory_status(ssh, dir_paths)
            if dir_status:
                metrics['directory_watch'] = dir_status
                logger.info(f"Directory watch data added to metrics: {len(dir_status)} entries")
            else:
                logger.warning("No directory watch data returned")
                metrics['directory_watch'] = []

            ssh.close()
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting metrics from {ip_address}: {e}")
            return {'error': str(e)}

    def get_directory_status(self, ssh, paths: list) -> list:
        """Get status and recent changes for monitored directories"""
        results = []
        logger.info(f"Checking directory status for paths: {paths}")
        
        for path in paths:
            try:
                logger.info(f"Checking directory: {path}")
                # Check if directory exists
                cmd = f"test -d {path} || echo 'NOT_FOUND'"
                stdin, stdout, stderr = ssh.exec_command(cmd)
                output = stdout.read().decode().strip()
                
                if output == 'NOT_FOUND':
                    logger.warning(f"Directory not found: {path}")
                    results.append({'path': path, 'status': 'missing'})
                    continue
                
                # Find the newest subfolder within the directory
                cmd = f"find {path} -maxdepth 1 -type d -not -path {path} -printf '%T@ %p\\n' 2>/dev/null | sort -nr | head -1 || echo 'NO_SUBFOLDERS'"
                stdin, stdout, stderr = ssh.exec_command(cmd)
                output = stdout.read().decode().strip()
                error_output = stderr.read().decode().strip()
                
                if error_output:
                    logger.warning(f"SSH error for {path}: {error_output}")
                
                logger.info(f"Newest subfolder search output for {path}: {output}")
                
                if output == 'NO_SUBFOLDERS' or not output:
                    logger.warning(f"No subfolders found in {path}")
                    results.append({
                        'path': path,
                        'status': 'ok',
                        'newest_folder_last_modified': None,
                        'newest_folder_size_mb': None,
                        'newest_folder_name': None,
                        'timestamp': timezone.now().isoformat()
                    })
                    continue
                
                # Parse the newest folder info: timestamp and path
                try:
                    timestamp, folder_path = output.split(' ', 1)
                    timestamp_float = float(timestamp)
                    
                    # Get folder size
                    size_cmd = f"du -sm {folder_path} 2>/dev/null | cut -f1 || echo '0'"
                    stdin, stdout, stderr = ssh.exec_command(size_cmd)
                    size_output = stdout.read().decode().strip()
                    folder_size_mb = float(size_output) if size_output.replace('.', '').isdigit() else 0.0
                    
                    # Extract folder name from full path
                    folder_name = folder_path.split('/')[-1]
                    
                    results.append({
                        'path': path,
                        'status': 'ok',
                        'newest_folder_last_modified': datetime.fromtimestamp(timestamp_float).isoformat(),
                        'newest_folder_size_mb': round(folder_size_mb, 2),
                        'newest_folder_name': folder_name,
                        'timestamp': timezone.now().isoformat()
                    })
                    logger.info(f"Directory {path} newest folder: {folder_name} ({folder_size_mb} MB)")
                    
                except (ValueError, IndexError) as e:
                    logger.error(f"Error parsing newest folder info for {path}: {e}")
                    results.append({
                        'path': path,
                        'status': 'error',
                        'error': f'Failed to parse folder info: {str(e)}'
                    })
                    
            except Exception as e:
                logger.error(f"Error checking directory {path}: {e}")
                results.append({'path': path, 'status': 'error', 'error': str(e)})
        
        logger.info(f"Directory status results: {results}")
        return results
    
    def get_cpu_usage(self, ssh) -> dict:
        """Get CPU usage via /proc/stat"""
        try:
            # Try /proc/stat method first (more reliable)
            stdin, stdout, stderr = ssh.exec_command("grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$4+$5)} END {print usage}'")
            cpu_output = stdout.read().decode().strip()
            
            if cpu_output:
                try:
                    cpu_percent = float(cpu_output)
                    return {
                        'usage_percent': cpu_percent,
                        'status': 'normal' if cpu_percent < 80 else 'high' if cpu_percent < 95 else 'critical',
                        'status_color': '#28a745' if cpu_percent < 80 else '#ffc107' if cpu_percent < 95 else '#dc3545'
                    }
                except ValueError:
                    pass
            
            # Fallback to top command if /proc/stat fails
            stdin, stdout, stderr = ssh.exec_command("top -bn1 | grep 'Cpu(s)' | sed 's/.*, *\\([0-9.]*\\)% id.*/\\1/' | head -1")
            cpu_output = stdout.read().decode().strip()
            
            if cpu_output and cpu_output.isdigit():
                cpu_percent = float(cpu_output)
                return {
                    'usage_percent': cpu_percent,
                    'status': 'normal' if cpu_percent < 80 else 'high' if cpu_percent < 95 else 'critical',
                    'status_color': '#28a745' if cpu_percent < 80 else '#ffc107' if cpu_percent < 95 else '#dc3545'
                }
            
            return {'error': 'Could not parse CPU usage', 'raw': cpu_output}
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_ram_usage(self, ssh) -> dict:
        """Get RAM usage via free command"""
        try:
            stdin, stdout, stderr = ssh.exec_command("free -m | grep '^Mem:' | awk '{print $3/$2 * 100.0}'")
            ram_output = stdout.read().decode().strip()
            
            if ram_output:
                ram_percent = float(ram_output)
                return {
                    'usage_percent': ram_percent,
                    'status': 'normal' if ram_percent < 80 else 'high' if ram_percent < 95 else 'critical',
                    'status_color': '#28a745' if ram_percent < 80 else '#ffc107' if ram_percent < 95 else '#dc3545'
                }
            
            return {'error': 'Could not parse RAM usage', 'raw': ram_output}
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_disk_usage(self, ssh) -> dict:
        """Get disk usage via df command"""
        try:
            # Use a more reliable disk command
            stdin, stdout, stderr = ssh.exec_command("df -h / | grep '^/dev/' | awk '{print $5}' | head -1")
            disk_output = stdout.read().decode().strip()
            
            if disk_output:
                try:
                    # The output is just "6%" so we need to parse it directly
                    disk_percent = float(disk_output.replace('%', ''))
                    return {
                        'usage_percent': disk_percent,
                        'status': 'normal' if disk_percent < 80 else 'high' if disk_percent < 95 else 'critical',
                        'status_color': '#28a745' if disk_percent < 80 else '#ffc107' if disk_percent < 95 else '#dc3545'
                    }
                except (ValueError, IndexError) as e:
                    # Fallback to parsing the whole line
                    try:
                        # Find the percentage in the line
                        for part in disk_output.split():
                            if '%' in part and part.replace('%', '').replace('.', '').isdigit():
                                disk_percent = float(part.replace('%', ''))
                                return {
                                    'usage_percent': disk_percent,
                                    'status': 'normal' if disk_percent < 80 else 'high' if disk_percent < 95 else 'critical',
                                    'status_color': '#28a745' if disk_percent < 80 else '#ffc107' if disk_percent < 95 else '#dc3545'
                                }
                        
                        # If we get here, no valid percentage was found
                        return {'error': 'Could not parse disk usage', 'raw': disk_output}
                    except ValueError:
                        return {'error': 'Could not parse disk usage', 'raw': disk_output}
                    except Exception as e:
                        return {'error': str(e)}
            
            return {'error': 'Could not get disk usage', 'raw': disk_output}
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_ssl_expiration(self, ssh, ip_address: str, server=None) -> list:
        """Get SSL certificate information for web servers"""
        from .ssl_certificate_monitor import SSLCertificateMonitor
        
        ssl_monitor = SSLCertificateMonitor()
        ssl_certificates = []
        
        try:
            logger.info(f"Getting SSL certificates for {ip_address}, server type: {server.server_type if server else 'None'}")
            
            # 1. Try SSH file check first if a custom path is specified (Most definitive)
            cert_path = None
            if server and server.ssl_cert_path:
                cert_path = server.ssl_cert_path
            
            if cert_path:
                logger.info(f"Checking custom certificate file via SSH: {cert_path}")
                # ... [same SSH code as before]
                stdin, stdout, stderr = ssh.exec_command(f"test -f {cert_path} && echo 'EXISTS' || echo 'NOT_FOUND'")
                file_check = stdout.read().decode().strip()
                
                if file_check == 'EXISTS':
                    logger.info(f"Certificate file exists: {cert_path}")
                    
                    # Get certificate expiration
                    stdin, stdout, stderr = ssh.exec_command(f"openssl x509 -in {cert_path} -noout -dates")
                    cert_output = stdout.read().decode().strip()
                    
                    if 'notAfter=' in cert_output:
                        # Parse expiration date
                        date_str = cert_output.split('notAfter=')[1].strip()
                        try:
                            # OpenSSL date format: "Dec 29 11:04:17 2025 GMT"
                            exp_date = datetime.strptime(date_str, '%b %d %H:%M:%S %Y GMT').replace(tzinfo=timezone.utc)
                            days_remaining = (exp_date - timezone.now()).days
                            
                            # Get certificate subject
                            stdin, stdout, stderr = ssh.exec_command(f"openssl x509 -in {cert_path} -noout -subject")
                            subject_output = stdout.read().decode().strip()
                            common_name = 'Unknown'
                            if '/CN=' in subject_output:
                                common_name = subject_output.split('/CN=')[1].split('/')[0]
                            
                            # Get certificate issuer
                            stdin, stdout, stderr = ssh.exec_command(f"openssl x509 -in {cert_path} -noout -issuer")
                            issuer_output = stdout.read().decode().strip()
                            issuer = 'Unknown'
                            if '/CN=' in issuer_output:
                                issuer = issuer_output.split('/CN=')[1].split('/')[0]
                            
                            ssl_certificates.append({
                                'hostname': ip_address,
                                'port': 443,
                                'path': cert_path,
                                'common_name': common_name,
                                'issuer': issuer,
                                'expiry_date': exp_date.strftime('%Y-%m-%d'),
                                'days_remaining': days_remaining,
                                'status': 'expired' if days_remaining < 0 else 'critical' if days_remaining < 7 else 'warning' if days_remaining < 30 else 'good',
                                'status_color': '#dc3545' if days_remaining < 0 else '#ffc107' if days_remaining < 7 else '#ff9800' if days_remaining < 30 else '#28a745',
                                'subject_common_name': common_name,
                                'issuer_common_name': issuer,
                                'checked_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'connection_method': 'ssh_file'
                            })
                            logger.info(f"SSL certificate processed via SSH for {ip_address}: {common_name}, {days_remaining} days remaining")
                        except ValueError as e:
                            logger.error(f"Could not parse certificate date for {ip_address}: {e}")
                    else:
                        logger.warning(f"Could not find certificate expiration date for {ip_address}")
                else:
                    logger.warning(f"Certificate file not found via SSH: {cert_path}")

            # 2. If no cert found via SSH, try direct SSL connection
            if not ssl_certificates:
                try:
                    # Check port 443 by default
                    ssl_info = ssl_monitor.get_ssl_info(ip_address, 443)
                    if ssl_info:
                        formatted_cert = ssl_monitor.format_certificate_info(ssl_info)
                        ssl_certificates.append(formatted_cert)
                        logger.info(f"SSL certificate found via direct connection for {ip_address}:443")
                except Exception as e:
                    logger.debug(f"Direct SSL connection failed for {ip_address}:443 - {e}")
            
            logger.info(f"Total SSL certificates found for {ip_address}: {len(ssl_certificates)}")
            return ssl_certificates
            
        except Exception as e:
            logger.error(f"Error getting SSL certificate for {ip_address}: {e}")
            return []
    
    def get_cached_metrics(self, ip_address: str) -> dict:
        """Get cached metrics for a device"""
        cache_key = f'device_metrics_{ip_address}'
        return cache.get(cache_key)
    
    def update_metrics_cache(self, ip_address: str, metrics: dict, changes: dict):
        """Update metrics cache with change tracking"""
        cache_key = f'device_metrics_{ip_address}'
        cache_data = {
            'metrics': metrics,
            'changes': changes,
            'timestamp': timezone.now().isoformat()
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, cache_data, timeout=300)
        
        # Also update global metrics cache
        global_cache_key = 'all_device_metrics'
        global_cached = cache.get(global_cache_key, {})
        global_cached[ip_address] = cache_data
        cache.set(global_cache_key, global_cached, timeout=300)
    
    def detect_changes(self, old_metrics: dict, new_metrics: dict) -> dict:
        """Detect changes between old and new metrics"""
        changes = {}
        
        # Compare CPU
        if 'cpu' in old_metrics and 'cpu' in new_metrics:
            old_cpu = old_metrics['cpu'].get('usage_percent', 0)
            new_cpu = new_metrics['cpu'].get('usage_percent', 0)
            if abs(old_cpu - new_cpu) > 5:  # 5% threshold
                changes['cpu'] = {
                    'old': old_cpu,
                    'new': new_cpu,
                    'change': new_cpu - old_cpu,
                    'direction': 'increase' if new_cpu > old_cpu else 'decrease'
                }
        
        # Compare RAM
        if 'ram' in old_metrics and 'ram' in new_metrics:
            old_ram = old_metrics['ram'].get('usage_percent', 0)
            new_ram = new_metrics['ram'].get('usage_percent', 0)
            if abs(old_ram - new_ram) > 5:  # 5% threshold
                changes['ram'] = {
                    'old': old_ram,
                    'new': new_ram,
                    'change': new_ram - old_ram,
                    'direction': 'increase' if new_ram > old_ram else 'decrease'
                }
        
        # Compare Disk
        if 'disk' in old_metrics and 'disk' in new_metrics:
            old_disk = old_metrics['disk'].get('usage_percent', 0)
            new_disk = new_metrics['disk'].get('usage_percent', 0)
            if abs(old_disk - new_disk) > 2:  # 2% threshold
                changes['disk'] = {
                    'old': old_disk,
                    'new': new_disk,
                    'change': new_disk - old_disk,
                    'direction': 'increase' if new_disk > old_disk else 'decrease'
                }
        
        # Compare SSL (SSL is a list of certificates)
        if 'ssl' in old_metrics and 'ssl' in new_metrics:
            old_ssl_list = old_metrics['ssl']
            new_ssl_list = new_metrics['ssl']
            
            if isinstance(old_ssl_list, list) and isinstance(new_ssl_list, list) and old_ssl_list and new_ssl_list:
                old_ssl = old_ssl_list[0].get('days_remaining', 0)
                new_ssl = new_ssl_list[0].get('days_remaining', 0)
                if abs(old_ssl - new_ssl) > 0:
                    changes['ssl'] = {
                        'old_days': old_ssl,
                        'new_days': new_ssl,
                        'change': new_ssl - old_ssl,
                        'direction': 'decrease' if new_ssl < old_ssl else 'increase'
                    }
        
        return changes
    
    def get_all_metrics_summary(self) -> dict:
        """Get summary of all device metrics"""
        cache_key = 'all_device_metrics'
        cached_data = cache.get(cache_key, {})
        
        summary = {
            'total_devices': len(cached_data),
            'devices': {},
            'alerts': {
                'critical_cpu': 0,
                'critical_ram': 0,
                'critical_disk': 0,
                'expired_ssl': 0
            }
        }
        
        for ip_address, data in cached_data.items():
            metrics = data.get('metrics', {})
            changes = data.get('changes', {})
            
            device_summary = {
                'ip_address': ip_address,
                'timestamp': data.get('timestamp'),
                'metrics': metrics,
                'changes': changes
            }
            
            summary['devices'][ip_address] = device_summary
            
            # Count alerts
            if 'cpu' in metrics and metrics['cpu'].get('status') == 'critical':
                summary['alerts']['critical_cpu'] += 1
            
            if 'ram' in metrics and metrics['ram'].get('status') == 'critical':
                summary['alerts']['critical_ram'] += 1
            
            if 'disk' in metrics and metrics['disk'].get('status') == 'critical':
                summary['alerts']['critical_disk'] += 1
            
            if 'ssl' in metrics and metrics['ssl'].get('status') == 'expired':
                summary['alerts']['expired_ssl'] += 1
        
        return summary

    def get_performance_trend(self, server, hours=24) -> dict:
        """Get performance trend data for a server, prioritizing agent-sourced metrics"""
        from monitor.models_metrics import ServerMetrics
        from monitor.models import ResourceSample, CheckResult, DiskUsageSample
        
        since = timezone.now() - timedelta(hours=hours)
        
        # Initialize result with latency trend as it's always available via polling
        checks = CheckResult.objects.filter(
            server=server,
            checked_at__gte=since
        ).order_by('checked_at')
        
        latency_trend = [{'x': c.checked_at.isoformat(), 'y': c.latency_ms} for c in checks if c.latency_ms is not None]
        
        # 1. Try agent metrics first
        agent_metrics = ServerMetrics.objects.filter(
            server=server,
            timestamp__gte=since
        ).order_by('timestamp')
        
        if agent_metrics.exists():
            return {
                'cpu': [{'x': m.timestamp.isoformat(), 'y': m.cpu_percent} for m in agent_metrics if m.cpu_percent is not None],
                'ram': [{'x': m.timestamp.isoformat(), 'y': m.memory_percent} for m in agent_metrics if m.memory_percent is not None],
                'disk': [{'x': m.timestamp.isoformat(), 'y': m.disk_percent} for m in agent_metrics if m.disk_percent is not None],
                'load': [{'x': m.timestamp.isoformat(), 'y': m.load_1m} for m in agent_metrics if m.load_1m is not None],
                'network_in': [{'x': m.timestamp.isoformat(), 'y': m.network_bytes_recv} for m in agent_metrics if m.network_bytes_recv is not None],
                'network_out': [{'x': m.timestamp.isoformat(), 'y': m.network_bytes_sent} for m in agent_metrics if m.network_bytes_sent is not None],
                'latency': latency_trend,
                'source': 'agent'
            }
            
        # 2. Fallback to legacy ResourceSample
        res_samples = ResourceSample.objects.filter(
            server=server,
            collected_at__gte=since
        ).order_by('collected_at')
        
        disk_samples = DiskUsageSample.objects.filter(
            server=server,
            collected_at__gte=since
        ).order_by('collected_at')
        
        return {
            'cpu': [{'x': s.collected_at.isoformat(), 'y': s.cpu_percent} for s in res_samples if s.cpu_percent is not None],
            'ram': [{'x': s.collected_at.isoformat(), 'y': s.ram_percent} for s in res_samples if s.ram_percent is not None],
            'disk': [{'x': s.collected_at.isoformat(), 'y': s.percent} for s in disk_samples if s.percent is not None],
            'load': [{'x': s.collected_at.isoformat(), 'y': s.load_1} for s in res_samples if s.load_1 is not None],
            'latency': latency_trend,
            'source': 'legacy'
        }
