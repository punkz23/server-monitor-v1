#!/usr/bin/env python
"""Check detailed SSL certificate information"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.services.remote_ssl_certificate_monitor import RemoteSSLCertificateMonitor

def check_detailed_certs():
    print('=== Detailed SSL Certificate Information ===')
    
    remote_monitor = RemoteSSLCertificateMonitor()
    
    for ip in ['192.168.254.13', '192.168.254.50', '192.168.253.15']:
        print(f'\n🔍 Checking {ip}:')
        
        try:
            cert_info = remote_monitor.get_remote_ssl_info(ip)
            
            if cert_info:
                formatted = remote_monitor.format_certificate_info(cert_info)
                print(f'✅ Server: {formatted.get("server_name", "Unknown")}')
                print(f'📄 Subject: {formatted.get("subject_common_name", "Unknown")}')
                print(f'🏢 Issuer: {formatted.get("issuer_common_name", "Unknown")}')
                print(f'📅 Issued: {formatted.get("issued_date", "Unknown")}')
                print(f'📅 Expires: {formatted.get("expiry_date", "Unknown")}')
                print(f'⏰ Days Remaining: {formatted.get("days_remaining", "Unknown")}')
                print(f'🔍 Status: {formatted.get("status", "Unknown")}')
                print(f'🔧 Method: {formatted.get("connection_method", "Unknown")}')
            else:
                print('❌ No certificate data found')
                
        except Exception as e:
            print(f'❌ Error: {e}')

if __name__ == '__main__':
    check_detailed_certs()
