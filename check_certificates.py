#!/usr/bin/env python3
"""
Management command to check all SSL certificates
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
    """Check all enabled certificates"""
    
    monitor = CertificateMonitor()
    
    print("Checking all enabled SSL certificates...")
    print("=" * 50)
    
    results = monitor.check_all_certificates()
    
    success_count = len([r for r in results if r['status'] == 'success'])
    error_count = len([r for r in results if r['status'] in ['error', 'failed']])
    
    print(f"\nResults:")
    print(f"✅ Successfully checked: {success_count}")
    print(f"❌ Errors/Failed: {error_count}")
    print(f"📊 Total certificates: {len(results)}")
    
    # Show details for certificates with issues
    print("\nCertificate Details:")
    print("-" * 50)
    
    for result in results:
        cert = result['certificate']
        status_icon = "✅" if result['status'] == 'success' else "❌"
        
        print(f"{status_icon} {cert.name} ({cert.domain})")
        print(f"   Days until expiry: {cert.days_until_expiry}")
        print(f"   Status: {cert.get_status_text()}")
        
        if result['status'] != 'success':
            print(f"   Error: {result.get('error', 'Unknown error')}")
        
        print()
    
    # Get summary
    summary = monitor.get_certificate_status_summary()
    print("Summary:")
    print("-" * 50)
    print(f"Total certificates: {summary['total']}")
    print(f"Valid: {summary['valid']}")
    print(f"Warning (≤30 days): {summary['warning']}")
    print(f"Critical (≤7 days): {summary['critical']}")
    print(f"Expired: {summary['expired']}")
    
    return 0

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
