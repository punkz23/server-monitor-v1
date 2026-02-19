from django.core.management.base import BaseCommand
from django.utils import timezone
from monitor.models import NetworkDevice
from monitor.services.sophos_service import SophosMonitoringService
import time
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Monitor Sophos XGS126 devices and update their status'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=300,  # 5 minutes
            help='Polling interval in seconds (default: 300)'
        )
        parser.add_argument(
            '--device-id',
            type=int,
            help='Specific device ID to monitor (default: all Sophos devices)'
        )
    
    def handle(self, *args, **options):
        interval = options['interval']
        device_id = options.get('device_id')
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting Sophos monitoring service (interval: {interval}s)')
        )
        
        try:
            while True:
                self._monitor_devices(device_id)
                time.sleep(interval)
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS('Stopping Sophos monitoring service'))
        except Exception as e:
            logger.error(f"Monitoring service error: {str(e)}")
            raise
    
    def _monitor_devices(self, device_id=None):
        """Monitor all Sophos devices or a specific one"""
        devices = NetworkDevice.objects.filter(device_type='FIREWALL', enabled=True)
        
        if device_id:
            devices = devices.filter(id=device_id)
        
        for device in devices:
            try:
                self.stdout.write(f"Updating {device.name} ({device.ip_address})...")
                service = SophosMonitoringService(device)
                success = service.update_device_status()
                
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(f"Successfully updated {device.name}")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f"Failed to update {device.name}")
                    )
                    
            except Exception as e:
                logger.error(f"Error monitoring device {device.name}: {str(e)}")
                self.stdout.write(
                    self.style.ERROR(f"Error monitoring {device.name}: {str(e)}")
                )
