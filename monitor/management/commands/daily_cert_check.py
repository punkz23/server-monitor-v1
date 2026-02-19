from django.core.management.base import BaseCommand
from django.utils import timezone
from monitor.services.certificate_monitor import CertificateMonitor


class Command(BaseCommand):
    help = 'Daily automated SSL certificate check and alerting'

    def handle(self, *args, **options):
        self.stdout.write("Starting daily SSL certificate check...")
        self.stdout.write("=" * 50)
        
        monitor = CertificateMonitor()
        
        # Check all certificates
        results = monitor.check_all_certificates()
        
        success_count = len([r for r in results if r['status'] == 'success'])
        error_count = len([r for r in results if r['status'] in ['error', 'failed']])
        
        self.stdout.write(f"Results:")
        self.stdout.write(f"✅ Successfully checked: {success_count}")
        self.stdout.write(f"❌ Errors/Failed: {error_count}")
        self.stdout.write(f"📊 Total certificates: {len(results)}")
        
        # Get summary for logging
        summary = monitor.get_certificate_status_summary()
        
        self.stdout.write(f"\nSummary:")
        self.stdout.write(f"Total certificates: {summary['total']}")
        self.stdout.write(f"Valid: {summary['valid']}")
        self.stdout.write(f"Warning (≤30 days): {summary['warning']}")
        self.stdout.write(f"Critical (≤7 days): {summary['critical']}")
        self.stdout.write(f"Expired: {summary['expired']}")
        
        # Log certificates with issues
        if summary['warning'] > 0 or summary['critical'] > 0 or summary['expired'] > 0:
            self.stdout.write(f"\nCertificates requiring attention:")
            self.stdout.write("-" * 50)
            
            for cert_data in summary['certificates']:
                if cert_data['status'] in ['warning', 'critical', 'expired']:
                    status_icon = "⚠️" if cert_data['status'] == 'warning' else "❌"
                    self.stdout.write(
                        f"{status_icon} {cert_data['name']} ({cert_data['domain']}) - "
                        f"{cert_data['days_until_expiry']} days until expiry"
                    )
        
        # Exit with appropriate code for automation
        if summary['critical'] > 0 or summary['expired'] > 0:
            self.stdout.write(self.style.ERROR("\n🚨 CRITICAL: Some certificates require immediate attention!"))
            exit_code = 2  # Critical
        elif summary['warning'] > 0:
            self.stdout.write(self.style.WARNING("\n⚠️ WARNING: Some certificates will expire soon"))
            exit_code = 1  # Warning
        else:
            self.stdout.write(self.style.SUCCESS("\n✅ All certificates are in good status"))
            exit_code = 0  # Success
        
        self.stdout.write(f"\nDaily certificate check completed at {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Return exit code for automation
        if exit_code != 0:
            raise SystemExit(exit_code)
        return exit_code
