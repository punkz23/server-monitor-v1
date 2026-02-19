from django.core.management.base import BaseCommand
from monitor.services.server_status_monitor import start_automated_monitoring, stop_automated_monitoring, get_server_monitor
import time
import signal
import sys


class Command(BaseCommand):
    help = 'Start or stop automated server status monitoring'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            type=str,
            choices=['start', 'stop', 'status', 'run'],
            help='Action to perform: start, stop, status, or run',
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=300,
            help='Check interval in seconds (default: 300)',
        )

    def handle(self, *args, **options):
        action = options['action']
        interval = options['interval']
        
        if action == 'start':
            self.start_monitoring(interval)
        elif action == 'stop':
            self.stop_monitoring()
        elif action == 'status':
            self.show_status()
        elif action == 'run':
            self.run_forever(interval)

    def start_monitoring(self, interval):
        """Start automated monitoring in background"""
        monitor = get_server_monitor()
        monitor.check_interval = interval
        
        if monitor.running:
            self.stdout.write(self.style.WARNING('⚠️ Automated monitoring is already running'))
            return
        
        monitor.start()
        self.stdout.write(self.style.SUCCESS(f'✅ Automated monitoring started (interval: {interval}s)'))
        self.stdout.write('💡 Use "python manage.py monitor_status stop" to stop')

    def stop_monitoring(self):
        """Stop automated monitoring"""
        monitor = get_server_monitor()
        
        if not monitor.running:
            self.stdout.write(self.style.WARNING('⚠️ Automated monitoring is not running'))
            return
        
        monitor.stop()
        self.stdout.write(self.style.SUCCESS('✅ Automated monitoring stopped'))

    def show_status(self):
        """Show current monitoring status"""
        monitor = get_server_monitor()
        
        if monitor.running:
            self.stdout.write(self.style.SUCCESS(f'✅ Automated monitoring is running'))
            self.stdout.write(f'⏱️ Check interval: {monitor.check_interval} seconds')
            self.stdout.write(f'🧵 Thread: {monitor.thread.name if monitor.thread else "Unknown"}')
        else:
            self.stdout.write(self.style.WARNING('⚠️ Automated monitoring is not running'))
        
        # Show recent server status
        from monitor.models import Server
        from django.utils import timezone
        from datetime import timedelta
        
        recent_time = timezone.now() - timedelta(minutes=10)
        recent_servers = Server.objects.filter(last_checked__gte=recent_time)
        
        self.stdout.write(f'\n📊 Recently checked servers (last 10 min): {recent_servers.count()}')
        
        up_count = recent_servers.filter(last_status='UP').count()
        down_count = recent_servers.filter(last_status='DOWN').count()
        
        self.stdout.write(f'🟢 Up: {up_count}')
        self.stdout.write(f'🔴 Down: {down_count}')
        
        if recent_servers.exists():
            uptime = round((up_count / recent_servers.count() * 100), 1)
            self.stdout.write(f'📈 Uptime: {uptime}%')

    def run_forever(self, interval):
        """Run monitoring in foreground (for testing)"""
        self.stdout.write(f'🔄 Starting monitoring in foreground (interval: {interval}s)')
        self.stdout.write('💡 Press Ctrl+C to stop')
        
        monitor = get_server_monitor()
        monitor.check_interval = interval
        
        def signal_handler(signum, frame):
            self.stdout.write('\n🛑 Stopping monitoring...')
            monitor.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            monitor.start()
            while monitor.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stdout.write('\n🛑 Stopping monitoring...')
            monitor.stop()
