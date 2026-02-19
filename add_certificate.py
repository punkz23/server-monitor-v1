#!/usr/bin/env python3
"""
Script to add the ho.employee.dailyoverland.com certificate to the monitoring system
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.services.certificate_monitor import CertificateMonitor

def main():
    """Add the certificate from the user's request"""
    
    # Certificate information from the user's request
    cert_info = {
        'certificate_name': 'ho.employee.dailyoverland.com',
        'serial_number': '529951bce013239098a36f8948a143eb92d',
        'key_type': 'ECDSA',
        'domains': [
            'ho.employee.dailyoverland.com',
            'ho-dtr.dailyoverland.com', 
            'onlinebooking.dailyoverland.com',
            'w2.dailyoverland.com',
            'www.ho-dtr.dailyoverland.com',
            'www.ho.employee.dailyoverland.com',
            'www.onlinebooking.dailyoverland.com',
            'www.w2.dailyoverland.com'
        ],
        'expiry_date': '2026-02-24 04:42:37+00:00',
        'certificate_path': '/etc/letsencrypt/live/ho.employee.dailyoverland.com/fullchain.pem',
        'private_key_path': '/etc/letsencrypt/live/ho.employee.dailyoverland.com/privkey.pem'
    }
    
    # Create certificate monitor and add certificate
    monitor = CertificateMonitor()
    
    print("Adding certificate to monitoring system...")
    print(f"Certificate: {cert_info['certificate_name']}")
    print(f"Domains: {', '.join(cert_info['domains'])}")
    print(f"Expires: {cert_info['expiry_date']}")
    print(f"Days until expiry: 21 days")
    print()
    
    certificate = monitor.add_certificate_from_info(cert_info)
    
    if certificate:
        print("✅ Certificate added successfully!")
        print(f"Certificate ID: {certificate.id}")
        print(f"Name: {certificate.name}")
        print(f"Domain: {certificate.domain}")
        print(f"Days until expiry: {certificate.days_until_expiry}")
        print(f"Status: {certificate.get_status_text()}")
        print()
        
        # Check the certificate immediately
        print("Checking certificate status...")
        result = monitor.check_certificate(certificate)
        
        if result['status'] == 'success':
            print("✅ Certificate checked successfully!")
            print(f"Valid: {certificate.is_valid}")
            print(f"Days until expiry: {certificate.days_until_expiry}")
        else:
            print(f"❌ Certificate check failed: {result.get('error', 'Unknown error')}")
        
        # Create alerts if needed
        print("Creating alerts if needed...")
        monitor.create_expiry_alerts(certificate)
        print("Alert check completed.")
        
    else:
        print("❌ Failed to add certificate")
        return 1
    
    return 0

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
