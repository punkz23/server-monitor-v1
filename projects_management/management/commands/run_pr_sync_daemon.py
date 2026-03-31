import time
import logging
from django.core.management.base import BaseCommand
from django.core.management import call_command

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Runs a background loop to periodically sync PRs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=3600,
            help='Interval between syncs in seconds (default: 3600)',
        )

    def handle(self, *args, **options):
        interval = options['interval']
        self.stdout.write(self.style.SUCCESS(f"Starting PR sync daemon with {interval}s interval..."))
        
        try:
            while True:
                self.stdout.write(f"Triggering PR sync at {time.strftime('%Y-%m-%d %H:%M:%S')}...")
                try:
                    call_command('sync_prs')
                except Exception as e:
                    logger.exception(f"Error in PR sync daemon: {e}")
                    self.stdout.write(self.style.ERROR(f"Error: {e}"))
                
                self.stdout.write(f"Sleeping for {interval}s...")
                time.sleep(interval)
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS("PR sync daemon stopped."))
