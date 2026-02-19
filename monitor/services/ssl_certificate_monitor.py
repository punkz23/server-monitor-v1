"""
SSL Certificate Monitoring Service
Monitors SSL certificate expiration dates for web servers
"""

import ssl
import socket
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class SSLCertificateMonitor:
    """Monitor SSL certificates for web servers"""
    
    def __init__(self):
        self.timeout = 10  # Connection timeout in seconds
    
    def get_ssl_info(self, hostname: str, port: int = 443) -> Optional[Dict]:
        """Get SSL certificate information for a hostname"""
        try:
            # Create SSL context that accepts self-signed certificates and hostname mismatches
            context = ssl.create_default_context()
            context.check_hostname = False  # Don't verify hostname for internal servers
            context.verify_mode = ssl.CERT_NONE  # Accept self-signed certificates
            
            # Connect to the server
            with socket.create_connection((hostname, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Extract certificate information
                    subject_dict = {}
                    issuer_dict = {}
                    
                    # Parse subject - certificate format: ((('field', 'value'),),)
                    try:
                        subject = cert.get('subject', [])
                        if subject and isinstance(subject, tuple):
                            for item_tuple in subject:
                                if isinstance(item_tuple, tuple) and len(item_tuple) > 0:
                                    item = item_tuple[0]
                                    if isinstance(item, tuple) and len(item) == 2:
                                        field, value = item
                                        subject_dict[field] = value
                    except Exception as e:
                        logger.warning(f"Error parsing subject: {e}")
                    
                    # Parse issuer - certificate format: ((('field', 'value'),),)
                    try:
                        issuer = cert.get('issuer', [])
                        if issuer and isinstance(issuer, tuple):
                            for item_tuple in issuer:
                                if isinstance(item_tuple, tuple) and len(item_tuple) > 0:
                                    item = item_tuple[0]
                                    if isinstance(item, tuple) and len(item) == 2:
                                        field, value = item
                                        issuer_dict[field] = value
                    except Exception as e:
                        logger.warning(f"Error parsing issuer: {e}")
                    
                    ssl_info = {
                        'hostname': hostname,
                        'port': port,
                        'subject': subject_dict,
                        'issuer': issuer_dict,
                        'version': cert.get('version'),
                        'serial_number': cert.get('serialNumber'),
                        'not_before': self._parse_date(cert.get('notBefore')),
                        'not_after': self._parse_date(cert.get('notAfter')),
                        'days_remaining': self._calculate_days_remaining(cert.get('notAfter')),
                        'is_valid': self._is_certificate_valid(cert),
                        'signature_algorithm': cert.get('signatureAlgorithm'),
                        'subject_alt_names': self._get_subject_alt_names(cert),
                        'fingerprint': self._get_fingerprint(cert),
                        'checked_at': datetime.now()
                    }
                    
                    logger.info(f"SSL certificate retrieved for {hostname}:{port}")
                    logger.debug(f"Certificate subject: {subject_dict}")
                    logger.debug(f"Certificate issuer: {issuer_dict}")
                    return ssl_info
                    
        except Exception as e:
            logger.error(f"Failed to get SSL certificate for {hostname}:{port} - {e}")
            return None
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse SSL certificate date string to datetime object"""
        try:
            if not date_str or date_str == 'None':
                return datetime.now()
            # SSL dates are in format: "MMM DD HH:MM:SS YYYY GMT"
            return datetime.strptime(date_str, '%b %d %H:%M:%S %Y GMT')
        except Exception as e:
            logger.error(f"Failed to parse date '{date_str}': {e}")
            return datetime.now()
    
    def _calculate_days_remaining(self, not_after: str) -> int:
        """Calculate days remaining until certificate expiration"""
        try:
            if not not_after or not_after == 'None':
                return -1
            expiry_date = self._parse_date(not_after)
            now = datetime.now()
            delta = expiry_date - now
            return delta.days
        except Exception:
            return -1
    
    def _is_certificate_valid(self, cert: Dict) -> bool:
        """Check if certificate is currently valid"""
        try:
            not_before = self._parse_date(cert.get('notBefore'))
            not_after = self._parse_date(cert.get('notAfter'))
            now = datetime.now()
            
            return not_before <= now <= not_after
        except Exception:
            return False
    
    def _get_subject_alt_names(self, cert: Dict) -> List[str]:
        """Extract Subject Alternative Names from certificate"""
        try:
            san_list = []
            for name_type, value in cert.get('subjectAltName', []):
                if name_type == 'DNS':
                    san_list.append(value)
            return san_list
        except Exception:
            return []
    
    def _get_fingerprint(self, cert: Dict) -> str:
        """Get certificate fingerprint"""
        try:
            # This is a simplified fingerprint calculation
            # In a real implementation, you'd calculate the actual SHA256 fingerprint
            return str(cert.get('serialNumber', ''))
        except Exception:
            return ''
    
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
        
        return {
            'hostname': ssl_info.get('hostname'),
            'port': ssl_info.get('port'),
            'subject_common_name': ssl_info.get('subject', {}).get('commonName', ''),
            'issuer_common_name': ssl_info.get('issuer', {}).get('commonName', ''),
            'issued_date': ssl_info.get('not_before').strftime('%Y-%m-%d') if ssl_info.get('not_before') else '',
            'expiry_date': ssl_info.get('not_after').strftime('%Y-%m-%d') if ssl_info.get('not_after') else '',
            'days_remaining': ssl_info.get('days_remaining', 0),
            'status': status,
            'status_color': self.get_status_color(status),
            'is_valid': ssl_info.get('is_valid', False),
            'signature_algorithm': ssl_info.get('signature_algorithm', ''),
            'subject_alt_names': ssl_info.get('subject_alt_names', []),
            'fingerprint': ssl_info.get('fingerprint', ''),
            'checked_at': ssl_info.get('checked_at').strftime('%Y-%m-%d %H:%M:%S') if ssl_info.get('checked_at') else ''
        }
