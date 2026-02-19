from django.core.management.base import BaseCommand
from django.utils import timezone
import logging

from monitor.isp_monitor import ISPMonitor, monitor_all_isps, get_isp_health_score
from monitor.models import ISPConnection

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Monitor ISP connections for latency, packet loss, and connectivity'

    def add_arguments(self, parser):
        parser.add_argument(
            '--isp-id',
            type=int,
            help='Monitor specific ISP connection by ID',
        )
        parser.add_argument(
            '--health-score',
            action='store_true',
            help='Show overall ISP health score',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose logging',
        )

    def handle(self, *args, **options):
        if options['verbose']:
            logging.basicConfig(level=logging.INFO)
        
        if options['health_score']:
            score = get_isp_health_score()
            self.stdout.write(
                self.style.SUCCESS(f"Overall ISP Health Score: {score}/100")
            )
            return

        if options['isp_id']:
            # Monitor specific ISP
            try:
                isp = ISPConnection.objects.get(id=options['isp_id'])
                monitor = ISPMonitor(isp)
                metrics = monitor.update_metrics()
                
                self.stdout.write(
                    self.style.SUCCESS(f"Updated {len(metrics)} metrics for {isp.name}")
                )
                
                # Show status summary
                summary = monitor.get_status_summary()
                self.stdout.write(f"Status: {summary['status']}")
                
            except ISPConnection.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"ISP connection with ID {options['isp_id']} not found")
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Failed to monitor ISP {options['isp_id']}: {e}")
                )
        else:
            # Monitor all enabled ISPs
            results = monitor_all_isps()
            
            total_isps = len(results)
            successful = sum(1 for r in results.values() if r['success'])
            failed = total_isps - successful
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Monitoring complete: {successful}/{total_isps} ISPs successful"
                )
            )
            
            if failed > 0:
                self.stdout.write(
                    self.style.WARNING(f"{failed} ISPs failed to monitor:")
                )
                for name, result in results.items():
                    if not result['success']:
                        self.stdout.write(f"  - {name}: {result.get('error', 'Unknown error')}")
            
            # Show health score
            score = get_isp_health_score()
            self.stdout.write(
                self.style.SUCCESS(f"Overall ISP Health Score: {score}/100")
            )
