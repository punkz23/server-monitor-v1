from django.core.management.base import BaseCommand
from monitor.services.certificate_monitor import CertificateMonitor


class Command(BaseCommand):
    help = 'Check all SSL certificates and create alerts if needed'

    def add_arguments(self, parser):
        parser.add_argument(
            '--certificate-id',
            type=int,
            help='Check specific certificate ID instead of all',
        )
        parser.add_argument(
            '--summary',
            action='store_true',
            help='Show summary only',
        )

    def handle(self, *args, **options):
        monitor = CertificateMonitor()
        
        if options['certificate_id']:
            # Check specific certificate
            try:
                from monitor.models import SSLCertificate
                certificate = SSLCertificate.objects.get(id=options['certificate_id'])
                
                self.stdout.write(f"Checking certificate: {certificate.name}")
                result = monitor.check_certificate(certificate)
                
                if result['status'] == 'success':
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ {certificate.name}: {certificate.get_status_text()}"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f"❌ {certificate.name}: {result.get('error', 'Unknown error')}"
                        )
                    )
                
                # Create alerts if needed
                monitor.create_expiry_alerts(certificate)
                
            except SSLCertificate.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Certificate with ID {options['certificate_id']} not found")
                )
                return
        else:
            # Check all certificates
            self.stdout.write("Checking all enabled SSL certificates...")
            self.stdout.write("=" * 50)
            
            results = monitor.check_all_certificates()
            
            success_count = len([r for r in results if r['status'] == 'success'])
            error_count = len([r for r in results if r['status'] in ['error', 'failed']])
            
            if not options['summary']:
                self.stdout.write(f"\nResults:")
                self.stdout.write(f"✅ Successfully checked: {success_count}")
                self.stdout.write(f"❌ Errors/Failed: {error_count}")
                self.stdout.write(f"📊 Total certificates: {len(results)}")
                
                # Show details for certificates with issues
                self.stdout.write("\nCertificate Details:")
                self.stdout.write("-" * 50)
                
                for result in results:
                    cert = result['certificate']
                    status_icon = "✅" if result['status'] == 'success' else "❌"
                    
                    self.stdout.write(f"{status_icon} {cert.name} ({cert.domain})")
                    self.stdout.write(f"   Days until expiry: {cert.days_until_expiry}")
                    self.stdout.write(f"   Status: {cert.get_status_text()}")
                    
                    if result['status'] != 'success':
                        self.stdout.write(f"   Error: {result.get('error', 'Unknown error')}")
                    
                    self.stdout.write("")
            
            # Get summary
            summary = monitor.get_certificate_status_summary()
            self.stdout.write("Summary:")
            self.stdout.write("-" * 50)
            self.stdout.write(f"Total certificates: {summary['total']}")
            
            if summary['valid'] > 0:
                self.stdout.write(self.style.SUCCESS(f"Valid: {summary['valid']}"))
            
            if summary['warning'] > 0:
                self.stdout.write(self.style.WARNING(f"Warning (≤30 days): {summary['warning']}"))
            
            if summary['critical'] > 0:
                self.stdout.write(self.style.ERROR(f"Critical (≤7 days): {summary['critical']}"))
            
            if summary['expired'] > 0:
                self.stdout.write(self.style.ERROR(f"Expired: {summary['expired']}"))
            
            # Exit with error code if there are critical or expired certificates
            if summary['critical'] > 0 or summary['expired'] > 0:
                exit_code = 1
            else:
                exit_code = 0
            
            return exit_code
