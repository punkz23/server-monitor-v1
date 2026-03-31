import logging
from django.core.management.base import BaseCommand
from monitor.models import SSLCertificate

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Disables SSL certificate checks for specific problematic IP addresses.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to disable problematic SSL certificate checks...'))
        
        PROBLEM_IPS = ['192.168.254.10', '192.168.254.7']
        
        certs_updated = 0
        
        for cert in SSLCertificate.objects.filter(domain__in=PROBLEM_IPS, enabled=True):
            self.stdout.write(f"Disabling SSL check for certificate '{cert.name}' (Domain: {cert.domain})...")
            cert.enabled = False
            cert.save(update_fields=['enabled'])
            certs_updated += 1

        if certs_updated > 0:
            self.stdout.write(self.style.SUCCESS(f'Successfully disabled {certs_updated} SSL certificate check(s).'))
        else:
            self.stdout.write(self.style.SUCCESS('No problematic SSL certificate checks needed disabling.'))
