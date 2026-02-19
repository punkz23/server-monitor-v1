#!/usr/bin/env python3
"""
Test script to check remote certificate for ho.employee.dailyoverland.com
"""

import ssl
import socket
from datetime import datetime, timezone
import OpenSSL

def check_remote_certificate(domain, port=443):
    """Check certificate from remote server"""
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        print(f"Connecting to {domain}:{port}...")
        with socket.create_connection((domain, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert_der = ssock.getpeercert(binary_form=True)
                cert_pem = ssl.DER_cert_to_PEM_cert(cert_der)
                
                print("✅ Successfully retrieved certificate!")
                
                # Parse certificate with OpenSSL
                cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert_pem)
                
                # Get certificate info
                subject = cert.get_subject()
                issuer = cert.get_issuer()
                
                print(f"Subject: {subject.CN if subject.CN else 'Unknown'}")
                print(f"Issuer: {issuer.CN if issuer.CN else 'Unknown'}")
                print(f"Serial Number: {cert.get_serial_number()}")
                
                # Parse dates
                not_before_str = cert.get_notBefore().decode('ascii')
                not_after_str = cert.get_notAfter().decode('ascii')
                
                not_before = datetime.strptime(not_before_str, '%Y%m%d%H%M%SZ').replace(tzinfo=timezone.utc)
                not_after = datetime.strptime(not_after_str, '%Y%m%d%H%M%SZ').replace(tzinfo=timezone.utc)
                
                print(f"Valid from: {not_before}")
                print(f"Valid until: {not_after}")
                
                # Calculate days until expiry
                now = datetime.now(timezone.utc)
                days_until_expiry = (not_after - now).days
                print(f"Days until expiry: {days_until_expiry}")
                
                # Get alternative names
                try:
                    for i in range(cert.get_extension_count()):
                        ext = cert.get_extension(i)
                        if ext.get_short_name() == b'subjectAltName':
                            san_str = str(ext)
                            domains = [d.split(':')[1] for d in san_str.split(', ') if d.startswith('DNS:')]
                            print("Subject Alternative Names:")
                            for domain_name in domains:
                                print(f"  DNS: {domain_name}")
                            break
                except Exception as e:
                    print(f"Error parsing SAN: {e}")
                
                return True
                
    except Exception as e:
        print(f"❌ Error checking certificate: {e}")
        return False

if __name__ == '__main__':
    domain = "ho.employee.dailyoverland.com"
    check_remote_certificate(domain)
