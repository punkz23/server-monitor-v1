"""
Remote SSL Certificate Monitor via SSH
Monitors SSL certificates on remote servers using SSH connections
"""

import logging
import paramiko
import subprocess
import re
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class RemoteSSLCertificateMonitor:
    """Monitor SSL certificates on remote servers via SSH"""
    
    def __init__(self):
        self.timeout = 10
        self.ssh_credentials = {
            '192.168.254.13': {
                'username': 'w4-assistant',
                'password': 'O6G1Amvos0icqGRC',
                'cert_path': '/etc/letsencrypt/live/dailyoverland.com/',
                'server_name': 'onlinebooking'
            },
            '192.168.254.50': {
                'username': 'ws3-assistant',
                'password': '6c$7TpzjzYpTpbDp',
                'cert_path': '/etc/letsencrypt/live/id.dailyoverland.com/',
                'server_name': 'webserver3'
            },
            '192.168.253.15': {
                'username': 'w1-assistant',
                'password': 'hIkLM#X5x1sjwIrM',
                'cert_path': '/etc/letsencrypt/live/ho.employee.dailyoverland.com/',
                'server_name': 'w1'
            }
        }
    
    def get_remote_ssl_info(self, ip_address: str) -> Optional[Dict]:
        """Get SSL certificate information from remote server via SSH"""
        try:
            if ip_address not in self.ssh_credentials:
                logger.warning(f"No SSH credentials configured for {ip_address}")
                return None
            
            creds = self.ssh_credentials[ip_address]
            
            # Create SSH client
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            try:
                # Connect to remote server
                ssh.connect(
                    hostname=ip_address,
                    username=creds['username'],
                    password=creds['password'],
                    timeout=self.timeout,
                    allow_agent=False,
                    look_for_keys=False
                )
                
                # Get certificate information using direct SSL connection
                cert_info = self._get_cert_via_ssl_connection(ssh, ip_address, creds['server_name'])
                
                if cert_info:
                    cert_info['server_name'] = creds['server_name']
                    cert_info['connection_method'] = 'ssh_ssl'
                    logger.info(f"Remote SSL certificate retrieved for {ip_address} via SSH+SSL")
                    return cert_info
                else:
                    logger.warning(f"No certificate data found for {ip_address}")
                    return None
                    
            finally:
                ssh.close()
                
        except Exception as e:
            logger.error(f"Failed to get remote SSL certificate for {ip_address}: {e}")
            return None
    
    def _get_cert_via_ssl_connection(self, ssh, ip_address: str, server_name: str) -> Optional[Dict]:
        """Get certificate info by reading certificate files directly"""
        try:
            # Map server names to their certificate paths (try both live and archive)
            cert_paths = {
                'onlinebooking': [
                    '/etc/letsencrypt/live/dailyoverland.com/cert.pem',
                    '/etc/letsencrypt/archive/dailyoverland.com/cert23.pem',
                    '/etc/letsencrypt/archive/dailyoverland.com/cert*.pem'
                ],
                'webserver3': [
                    '/etc/letsencrypt/live/id.dailyoverland.com/cert.pem',
                    '/etc/letsencrypt/archive/id.dailyoverland.com/cert14.pem',
                    '/etc/letsencrypt/archive/id.dailyoverland.com/cert*.pem'
                ],
                'w1': [
                    '/etc/letsencrypt/live/ho.employee.dailyoverland.com/cert.pem',
                    '/etc/letsencrypt/archive/ho.employee.dailyoverland.com/cert4.pem',
                    '/etc/letsencrypt/archive/ho.employee.dailyoverland.com/cert*.pem'
                ]
            }
            
            paths_to_try = cert_paths.get(server_name, [])
            cert_data = {}
            
            for cert_path in paths_to_try:
                if '*' in cert_path:
                    # Find the latest cert file
                    stdin, stdout, stderr = ssh.exec_command(f"ls -t {cert_path} 2>/dev/null | head -1")
                    latest_cert = stdout.read().decode().strip()
                    if latest_cert:
                        cert_path = latest_cert
                    else:
                        continue
                
                # Try to read certificate file (without sudo first)
                commands = [
                    f"openssl x509 -in {cert_path} -noout -subject 2>/dev/null",
                    f"openssl x509 -in {cert_path} -noout -issuer 2>/dev/null", 
                    f"openssl x509 -in {cert_path} -noout -dates 2>/dev/null",
                    f"openssl x509 -in {cert_path} -noout -serial 2>/dev/null",
                    f"openssl x509 -in {cert_path} -noout -fingerprint -sha256 2>/dev/null"
                ]
                
                for cmd in commands:
                    try:
                        stdin, stdout, stderr = ssh.exec_command(cmd)
                        output = stdout.read().decode().strip()
                        error = stderr.read().decode().strip()
                        
                        if output:
                            if "subject=" in output:
                                cert_data['subject'] = output
                            elif "issuer=" in output:
                                cert_data['issuer'] = output
                            elif "notBefore=" in output and "notAfter=" in output:
                                lines = output.split('\n')
                                for line in lines:
                                    if "notBefore=" in line:
                                        cert_data['not_before'] = line.strip()
                                    elif "notAfter=" in line:
                                        cert_data['not_after'] = line.strip()
                            elif "serial=" in output:
                                cert_data['serial'] = output
                            elif "SHA256 Fingerprint=" in output:
                                cert_data['fingerprint'] = output.replace("SHA256 Fingerprint=", "").strip().replace(':', '')
                        
                        # If we got subject and dates, break (we found a working cert)
                        if cert_data.get('subject') and cert_data.get('not_after'):
                            break
                            
                    except Exception as e:
                        logger.error(f"Error executing command '{cmd}': {e}")
                
                # If we got data, break from trying other paths
                if cert_data.get('subject') and cert_data.get('not_after'):
                    break
            
            if cert_data.get('subject') and cert_data.get('not_after'):
                # Create structured certificate info
                parsed_cert = {
                    'hostname': ip_address,
                    'port': 443,
                    'subject': self._parse_dn(cert_data.get('subject', '')),
                    'issuer': self._parse_dn(cert_data.get('issuer', '')),
                    'not_before': self._parse_openssl_date(cert_data.get('not_before', '')),
                    'not_after': self._parse_openssl_date(cert_data.get('not_after', '')),
                    'days_remaining': self._calculate_days_remaining_from_date(cert_data.get('not_after', '')),
                    'is_valid': self._is_certificate_valid_from_dates(cert_data.get('not_before', ''), cert_data.get('not_after', '')),
                    'signature_algorithm': 'RSA',  # Default for Let's Encrypt
                    'subject_alt_names': [],  # Not available from this method
                    'fingerprint': cert_data.get('fingerprint', ''),
                    'serial_number': cert_data.get('serial', '').replace('serial=', '').strip(),
                    'checked_at': datetime.now()
                }
                
                logger.info(f"Certificate read from file for {ip_address}: {parsed_cert.get('days_remaining')} days remaining")
                return parsed_cert
            
            logger.warning(f"Could not read certificate data for {server_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error reading certificate file: {e}")
            return None
    
    def _parse_openssl_output(self, ssl_output: str) -> Dict:
        """Parse openssl s_client output"""
        try:
            cert_data = {}
            
            lines = ssl_output.split('\n')
            for line in lines:
                line = line.strip()
                
                if line.startswith('subject='):
                    cert_data['subject'] = line.replace('subject=', '')
                elif line.startswith('issuer='):
                    cert_data['issuer'] = line.replace('issuer=', '')
                elif line.startswith('notBefore='):
                    cert_data['not_before'] = line.replace('notBefore=', '')
                elif line.startswith('notAfter='):
                    cert_data['not_after'] = line.replace('notAfter=', '')
                elif 'Signature Algorithm' in line:
                    cert_data['signature_algorithm'] = line.split(':')[0].strip()
                elif line.startswith('serial='):
                    cert_data['serial'] = line.replace('serial=', '')
            
            return cert_data
            
        except Exception as e:
            logger.error(f"Error parsing openssl output: {e}")
            return {}
    
    def _calculate_days_remaining_from_date(self, not_after_str: str) -> int:
        """Calculate days remaining from date string"""
        try:
            if not not_after_str:
                return -1
            
            expiry_date = self._parse_openssl_date(not_after_str)
            now = datetime.now()
            delta = expiry_date - now
            return delta.days
            
        except Exception:
            return -1
    
    def _is_certificate_valid_from_dates(self, not_before_str: str, not_after_str: str) -> bool:
        """Check if certificate is valid from date strings"""
        try:
            if not not_before_str or not not_after_str:
                return False
            
            not_before = self._parse_openssl_date(not_before_str)
            not_after = self._parse_openssl_date(not_after_str)
            now = datetime.now()
            
            return not_before <= now <= not_after
            
        except Exception:
            return False
    
    def _extract_certificate_info(self, ssh, cert_path: str, ip_address: str) -> Optional[Dict]:
        """Extract certificate information from remote server"""
        try:
            # Check if certificate directory exists
            stdin, stdout, stderr = ssh.exec_command(f"test -d {cert_path} && echo 'exists' || echo 'not_found'")
            result = stdout.read().decode().strip()
            
            if result != 'exists':
                logger.warning(f"Certificate directory not found: {cert_path}")
                return None
            
            # Get certificate file paths
            cert_file = f"{cert_path}cert.pem"
            
            # Check if certificate file exists
            stdin, stdout, stderr = ssh.exec_command(f"test -f {cert_file} && echo 'exists' || echo 'not_found'")
            result = stdout.read().decode().strip()
            
            if result != 'exists':
                logger.warning(f"Certificate file not found: {cert_file}")
                return None
            
            # Get certificate details using openssl
            commands = {
                'subject': f"openssl x509 -in {cert_file} -noout -subject",
                'issuer': f"openssl x509 -in {cert_file} -noout -issuer",
                'dates': f"openssl x509 -in {cert_file} -noout -dates",
                'serial': f"openssl x509 -in {cert_file} -noout -serial",
                'fingerprint': f"openssl x509 -in {cert_file} -noout -fingerprint -sha256",
                'sans': f"openssl x509 -in {cert_file} -noout -ext subjectAltName"
            }
            
            cert_data = {}
            
            for key, command in commands.items():
                try:
                    stdin, stdout, stderr = ssh.exec_command(command)
                    output = stdout.read().decode().strip()
                    error = stderr.read().decode().strip()
                    
                    if error:
                        logger.warning(f"Error getting {key} for {ip_address}: {error}")
                        cert_data[key] = None
                    else:
                        cert_data[key] = output
                        
                except Exception as e:
                    logger.error(f"Failed to execute command for {key}: {e}")
                    cert_data[key] = None
            
            # Parse certificate data
            parsed_cert = self._parse_certificate_data(cert_data, ip_address)
            
            return parsed_cert
            
        except Exception as e:
            logger.error(f"Error extracting certificate info: {e}")
            return None
    
    def _parse_certificate_data(self, cert_data: Dict, ip_address: str) -> Dict:
        """Parse raw certificate data into structured format"""
        try:
            # Parse subject
            subject = self._parse_dn(cert_data.get('subject', ''))
            
            # Parse issuer
            issuer = self._parse_dn(cert_data.get('issuer', ''))
            
            # Parse dates
            not_before = self._parse_openssl_date(cert_data.get('dates', '').split('\n')[0] if cert_data.get('dates') else '')
            not_after = self._parse_openssl_date(cert_data.get('dates', '').split('\n')[1] if cert_data.get('dates') and '\n' in cert_data.get('dates', '') else '')
            
            # Calculate days remaining
            days_remaining = self._calculate_days_remaining(not_after)
            
            # Parse SANs
            sans = self._parse_sans(cert_data.get('sans', ''))
            
            # Get fingerprint
            fingerprint = cert_data.get('fingerprint', '').replace('SHA256 Fingerprint=', '').strip().replace(':', '')
            
            # Get serial number
            serial = cert_data.get('serial', '').replace('serial=', '').strip()
            
            return {
                'hostname': ip_address,
                'port': 443,
                'subject': subject,
                'issuer': issuer,
                'not_before': not_before,
                'not_after': not_after,
                'days_remaining': days_remaining,
                'is_valid': self._is_certificate_valid(not_before, not_after),
                'signature_algorithm': 'RSA',  # Default for Let's Encrypt
                'subject_alt_names': sans,
                'fingerprint': fingerprint,
                'serial_number': serial,
                'checked_at': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error parsing certificate data: {e}")
            return None
    
    def _parse_dn(self, dn_string: str) -> Dict:
        """Parse distinguished name string into dictionary"""
        try:
            if not dn_string:
                return {}
            
            # Remove prefix and parse
            dn_string = dn_string.replace('subject=', '').replace('issuer=', '')
            
            parts = dn_string.split('/')
            dn_dict = {}
            
            for part in parts:
                if '=' in part:
                    key, value = part.split('=', 1)
                    dn_dict[key.strip()] = value.strip()
            
            return dn_dict
            
        except Exception as e:
            logger.error(f"Error parsing DN: {e}")
            return {}
    
    def _parse_openssl_date(self, date_str: str) -> datetime:
        """Parse OpenSSL date format"""
        try:
            if not date_str or '=' not in date_str:
                return datetime.now()
            
            # Remove prefix and parse
            date_str = date_str.split('=', 1)[1].strip()
            
            # Try different date formats
            date_formats = [
                '%b %d %H:%M:%S %Y GMT',  # Standard OpenSSL format
                '%b %d %H:%M:%S %Y GMT',  # Same format (backup)
                '%b %d %H:%M:%S %Y %Z',   # With timezone
                '%Y-%m-%d %H:%M:%S',      # ISO format
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            # If all formats fail, return current time
            logger.error(f"Could not parse date: '{date_str}'")
            return datetime.now()
            
        except Exception as e:
            logger.error(f"Error parsing date '{date_str}': {e}")
            return datetime.now()
    
    def _parse_sans(self, sans_string: str) -> List[str]:
        """Parse Subject Alternative Names"""
        try:
            if not sans_string:
                return []
            
            sans = []
            lines = sans_string.split('\n')
            
            for line in lines:
                if 'DNS:' in line:
                    dns_part = line.split('DNS:')[1].strip()
                    # Handle multiple DNS entries separated by commas
                    dns_entries = [entry.strip() for entry in dns_part.split(',')]
                    sans.extend(dns_entries)
            
            return list(set(sans))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error parsing SANs: {e}")
            return []
    
    def _calculate_days_remaining(self, not_after: datetime) -> int:
        """Calculate days remaining until certificate expiration"""
        try:
            if not not_after:
                return -1
            
            now = datetime.now()
            delta = not_after - now
            return delta.days
            
        except Exception:
            return -1
    
    def _is_certificate_valid(self, not_before: datetime, not_after: datetime) -> bool:
        """Check if certificate is currently valid"""
        try:
            if not not_before or not not_after:
                return False
            
            now = datetime.now()
            return not_before <= now <= not_after
            
        except Exception:
            return False
    
    def get_certificate_status(self, ssl_info: Dict) -> str:
        """Get certificate status based on expiration"""
        if not ssl_info:
            return 'error'
        
        days_remaining = ssl_info.get('days_remaining', 0)
        
        if days_remaining < 0:
            return 'expired'
        elif days_remaining <= 7:
            return 'critical'
        elif days_remaining <= 30:
            return 'warning'
        elif days_remaining <= 90:
            return 'info'
        else:
            return 'good'
    
    def get_status_color(self, status: str) -> str:
        """Get color code for certificate status"""
        colors = {
            'good': '#28a745',      # Green
            'info': '#17a2b8',      # Blue
            'warning': '#ffc107',   # Yellow
            'critical': '#fd7e14',  # Orange
            'expired': '#dc3545',   # Red
            'error': '#6c757d'      # Gray
        }
        return colors.get(status, '#6c757d')
    
    def format_certificate_info(self, ssl_info: Dict) -> Dict:
        """Format certificate information for display"""
        if not ssl_info:
            return {}
        
        status = self.get_certificate_status(ssl_info)
        subject = ssl_info.get('subject', {})
        issuer = ssl_info.get('issuer', {})
        
        return {
            'hostname': ssl_info.get('hostname'),
            'port': ssl_info.get('port', 443),
            'server_name': ssl_info.get('server_name', ''),
            'subject_common_name': subject.get('CN', ''),
            'issuer_common_name': issuer.get('CN', ''),
            'issued_date': ssl_info.get('not_before').strftime('%Y-%m-%d') if ssl_info.get('not_before') else '',
            'expiry_date': ssl_info.get('not_after').strftime('%Y-%m-%d') if ssl_info.get('not_after') else '',
            'days_remaining': ssl_info.get('days_remaining', 0),
            'status': status,
            'status_color': self.get_status_color(status),
            'is_valid': ssl_info.get('is_valid', False),
            'signature_algorithm': ssl_info.get('signature_algorithm', ''),
            'subject_alt_names': ssl_info.get('subject_alt_names', []),
            'fingerprint': ssl_info.get('fingerprint', ''),
            'serial_number': ssl_info.get('serial_number', ''),
            'connection_method': ssl_info.get('connection_method', 'unknown'),
            'checked_at': ssl_info.get('checked_at').strftime('%Y-%m-%d %H:%M:%S') if ssl_info.get('checked_at') else ''
        }
