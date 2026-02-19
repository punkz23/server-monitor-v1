from django.core.management.base import BaseCommand
from django.utils import timezone
import threading
import time
import signal
import sys
from monitor.management.commands.run_checks import Command as RunChecksCommand


class Command(BaseCommand):
    help = 'Run server checks continuously in the background'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stop_event = threading.Event()
        self._thread = None

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='Check interval in seconds (default: 60)'
        )
        parser.add_argument(
            '--timeout',
            type=float,
            default=3.0,
            help='Timeout for each check in seconds (default: 3.0)'
        )
        parser.add_argument(
            '--daemon',
            action='store_true',
            help='Run as a background daemon'
        )

    def handle(self, *args, **options):
        interval = options['interval']
        timeout = options['timeout']
        daemon = options['daemon']

        if daemon:
            self.stdout.write(self.style.SUCCESS(f'Starting server checks daemon with {interval}s interval'))
            
            # Set up signal handlers for graceful shutdown
            def signal_handler(signum, frame):
                self.stdout.write(self.style.WARNING('Received shutdown signal, stopping...'))
                self._stop_event.set()
                
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)

            # Run in background thread
            self._thread = threading.Thread(target=self._run_loop, args=(interval, timeout))
            self._thread.daemon = True
            self._thread.start()

            try:
                # Keep main thread alive
                while self._thread.is_alive():
                    time.sleep(1)
            except KeyboardInterrupt:
                self._stop_event.set()
                self._thread.join(timeout=5)
                
            self.stdout.write(self.style.SUCCESS('Server checks daemon stopped'))
        else:
            # Run once
            self._run_checks(timeout)

    def _run_loop(self, interval, timeout):
        """Main loop for running checks continuously"""
        run_checks_cmd = RunChecksCommand()
        
        # Run immediately on start
        self.stdout.write(self.style.SUCCESS('Running initial server checks...'))
        self._run_checks(timeout)
        
        while not self._stop_event.is_set():
            # Wait for the interval or stop event
            if self._stop_event.wait(interval):
                break
                
            if not self._stop_event.is_set():
                self.stdout.write(self.style.SUCCESS(f'Running scheduled server checks... ({timezone.now().strftime("%Y-%m-%d %H:%M:%S")})'))
                self._run_checks(timeout)

    def _run_checks(self, timeout):
        """Execute the run_checks command"""
        try:
            run_checks_cmd.handle(timeout=timeout, limit=0, interval=0.0)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error running checks: {e}'))
