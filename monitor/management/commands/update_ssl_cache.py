from django.core.management.base import BaseCommand
from monitor.services.ssl_cache_service import update_ssl_certificate_cache


class Command(BaseCommand):
    help = 'Update SSL certificate cache in background'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force cache update even if not expired',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        self.stdout.write('🔄 Updating SSL certificate cache...')
        
        try:
            update_ssl_certificate_cache()
            self.stdout.write(self.style.SUCCESS('✅ SSL certificate cache updated successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error updating SSL certificate cache: {e}'))
