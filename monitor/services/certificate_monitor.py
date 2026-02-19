import ssl
import socket
from datetime import datetime, timezone, timedelta
from django.utils import timezone as django_tz
from django.db import transaction
from monitor.models import SSLCertificate, AlertRule, AlertEvent, Server


class CertificateMonitor:
    """Service for monitoring SSL/TLS certificates"""
    
    def __init__(self):
        self.default_warning_days = 30
        self.default_critical_days = 7
    
    def check_all_certificates(self):
        """Check all enabled certificates"""
        certificates = SSLCertificate.objects.filter(enabled=True)
        results = []
        
        for cert in certificates:
            try:
                result = self.check_certificate(cert)
                results.append(result)
                
                # Create alerts if needed
                self.create_expiry_alerts(cert)
                
            except Exception as e:
                print(f"Error checking certificate {cert.name}: {e}")
                results.append({'certificate': cert, 'status': 'error', 'error': str(e)})
        
        return results
    
    def check_certificate(self, certificate):
        """Check a single certificate"""
        try:
            # Get certificate from file or remote server
            if certificate.cert_path and certificate.cert_path.startswith('/etc/letsencrypt/'):
                # Try remote checking for Let's Encrypt certificates that aren't accessible locally
                print(f"Certificate file not accessible locally, checking remote for {certificate.domain}")
                cert_data = self._get_remote_certificate(certificate.domain)
            else:
                cert_data = self._get_remote_certificate(certificate.domain)
            
            if cert_data:
                self._parse_certificate_data(certificate, cert_data)
                certificate.last_checked = django_tz.now()
                certificate.save()
                
                return {
                    'certificate': certificate,
                    'status': 'success',
                    'days_until_expiry': certificate.days_until_expiry,
                    'is_valid': certificate.is_valid
                }
            else:
                return {
                    'certificate': certificate,
                    'status': 'failed',
                    'error': 'Could not retrieve certificate'
                }
                
        except Exception as e:
            return {
                'certificate': certificate,
                'status': 'error',
                'error': str(e)
            }
    
    def _read_certificate_file(self, cert_path):
        """Read certificate from local file"""
        try:
            with open(cert_path, 'r') as f:
                cert_data = f.read()
            return cert_data
        except Exception as e:
            print(f"Error reading certificate file {cert_path}: {e}")
            return None
    
    def _get_remote_certificate(self, domain, port=443):
        """Get certificate from remote server"""
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((domain, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert_der = ssock.getpeercert(binary_form=True)
                    cert_pem = ssl.DER_cert_to_PEM_cert(cert_der)
                    return cert_pem
        except Exception as e:
            print(f"Error getting remote certificate for {domain}: {e}")
            return None
    
    def _parse_certificate_data(self, certificate, cert_data):
        """Parse certificate data and update model fields"""
        try:
            import OpenSSL
            
            # Parse certificate
            cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert_data)
            
            # Update basic info
            certificate.serial_number = cert.get_serial_number().__str__()
            certificate.issuer = cert.get_issuer().CN or 'Unknown'
            certificate.subject = cert.get_subject().CN or 'Unknown'
            
            # Parse dates
            not_before = datetime.strptime(cert.get_notBefore().decode('ascii'), '%Y%m%d%H%M%SZ').replace(tzinfo=timezone.utc)
            not_after = datetime.strptime(cert.get_notAfter().decode('ascii'), '%Y%m%d%H%M%SZ').replace(tzinfo=timezone.utc)
            
            certificate.issued_at = not_before
            certificate.expires_at = not_after
            
            # Calculate days until expiry
            now = django_tz.now()
            certificate.days_until_expiry = (not_after - now).days
            certificate.is_valid = now >= not_before and now < not_after
            
            # Check if self-signed
            certificate.is_self_signed = cert.get_issuer() == cert.get_subject()
            
            # Get alternative names
            try:
                for i in range(cert.get_extension_count()):
                    ext = cert.get_extension(i)
                    if ext.get_short_name() == b'subjectAltName':
                        san_str = str(ext)
                        domains = [d.split(':')[1] for d in san_str.split(', ') if d.startswith('DNS:')]
                        certificate.alternative_names = domains
                        break
            except:
                pass
            
        except Exception as e:
            print(f"Error parsing certificate data: {e}")
    
    def create_expiry_alerts(self, certificate):
        """Create alerts for certificates nearing expiry"""
        if not certificate.days_until_expiry:
            return
        
        # Check if we need to create alerts
        if certificate.days_until_expiry <= certificate.critical_days:
            self._create_alert_event(
                certificate,
                'CRITICAL',
                f'Certificate {certificate.name} expires in {certificate.days_until_expiry} days',
                'cert_expiry_critical'
            )
        elif certificate.days_until_expiry <= certificate.warning_days:
            self._create_alert_event(
                certificate,
                'WARNING',
                f'Certificate {certificate.name} expires in {certificate.days_until_expiry} days',
                'cert_expiry_warning'
            )
        elif certificate.days_until_expiry <= 0:
            self._create_alert_event(
                certificate,
                'CRITICAL',
                f'Certificate {certificate.name} has expired',
                'cert_expired'
            )
    
    def _create_alert_event(self, certificate, severity, message, alert_type):
        """Create an alert event for certificate expiry"""
        try:
            # Check if we already created an alert for this certificate recently
            recent_alerts = AlertEvent.objects.filter(
                title__contains=certificate.name,
                severity=severity,
                created_at__gte=django_tz.now() - timedelta(hours=24)
            )
            
            if recent_alerts.exists():
                return  # Already alerted recently
            
            # Create alert event
            AlertEvent.objects.create(
                server=None,  # Certificate alerts are not tied to specific servers
                rule=None,
                kind=alert_type,
                severity=severity,
                title=f'Certificate Expiry Alert',
                message=message,
                payload={
                    'certificate_id': certificate.id,
                    'certificate_name': certificate.name,
                    'domain': certificate.domain,
                    'days_until_expiry': certificate.days_until_expiry,
                    'expires_at': certificate.expires_at.isoformat() if certificate.expires_at else None
                }
            )
            
            print(f"Created {severity} alert for certificate {certificate.name}")
            
        except Exception as e:
            print(f"Error creating alert for certificate {certificate.name}: {e}")
    
    def add_certificate_from_info(self, cert_info):
        """Add a certificate from parsed certificate information"""
        try:
            # Parse expiry date
            expiry_date = datetime.strptime(cert_info['expiry_date'], '%Y-%m-%d %H:%M:%S%z')
            
            # Calculate days until expiry
            now = django_tz.now()
            days_until_expiry = (expiry_date - now).days
            
            # Create certificate record
            certificate = SSLCertificate.objects.create(
                name=cert_info['certificate_name'],
                domain=cert_info['domains'][0] if cert_info['domains'] else cert_info['certificate_name'],
                alternative_names=cert_info['domains'],
                serial_number=cert_info['serial_number'],
                key_type=cert_info['key_type'],
                cert_path=cert_info.get('certificate_path'),
                key_path=cert_info.get('private_key_path'),
                expires_at=expiry_date,
                days_until_expiry=days_until_expiry,
                is_valid=days_until_expiry > 0,
                warning_days=30,
                critical_days=7
            )
            
            print(f"Added certificate: {certificate.name}")
            return certificate
            
        except Exception as e:
            print(f"Error adding certificate: {e}")
            return None
    
    def get_certificate_status_summary(self):
        """Get summary of all certificate statuses"""
        certificates = SSLCertificate.objects.filter(enabled=True)
        
        summary = {
            'total': certificates.count(),
            'valid': 0,
            'warning': 0,
            'critical': 0,
            'expired': 0,
            'certificates': []
        }
        
        for cert in certificates:
            if not cert.is_valid or cert.days_until_expiry <= 0:
                summary['expired'] += 1
                status = 'expired'
            elif cert.days_until_expiry <= cert.critical_days:
                summary['critical'] += 1
                status = 'critical'
            elif cert.days_until_expiry <= cert.warning_days:
                summary['warning'] += 1
                status = 'warning'
            else:
                summary['valid'] += 1
                status = 'valid'
            
            summary['certificates'].append({
                'id': cert.id,
                'name': cert.name,
                'domain': cert.domain,
                'days_until_expiry': cert.days_until_expiry,
                'status': status,
                'expires_at': cert.expires_at
            })
        
        return summary
