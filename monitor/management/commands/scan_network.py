from django.core.management.base import BaseCommand
from django.utils import timezone
from monitor.services.network_scanner import NetworkScanner
from monitor.models import NetworkDevice
import logging

logger = logging.getLogger(__name__)

# Try to import Sophos scanner
try:
    from sophos_scanner_service import SophosNetworkScanner
    SOPHOS_AVAILABLE = True
except ImportError:
    SOPHOS_AVAILABLE = False

class Command(BaseCommand):
    help = 'Scan network for devices and update database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--network',
            type=str,
            help='Network range to scan (e.g., 192.168.1.0/24)',
        )
        parser.add_argument(
            '--timeout',
            type=int,
            default=3,
            help='Timeout for each host scan in seconds',
        )
        parser.add_argument(
            '--threads',
            type=int,
            default=50,
            help='Maximum number of concurrent threads',
        )
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Update existing devices with new information',
        )
        parser.add_argument(
            '--auto',
            action='store_true',
            help='Automatically detect local network ranges',
        )
        parser.add_argument(
            '--use-sophos',
            action='store_true',
            help='Use Sophos firewall for scanning (default: True if available)',
        )
        parser.add_argument(
            '--sophos-host',
            type=str,
            default='192.168.253.2',
            help='Sophos firewall IP address (default: 192.168.253.2)',
        )
        parser.add_argument(
            '--sophos-port',
            type=int,
            default=4444,
            help='Sophos firewall API port (default: 4444)',
        )
        parser.add_argument(
            '--sophos-username',
            type=str,
            default='francois_ignacio',
            help='Sophos firewall username (default: francois_ignacio)',
        )
    
    def handle(self, *args, **options):
        use_sophos = options['use_sophos'] and SOPHOS_AVAILABLE
        
        if use_sophos:
            # Use Sophos scanner
            from getpass import getpass
            password = getpass(f"Enter Sophos firewall password for {options['sophos_username']}: ")
            
            self.stdout.write("Using Sophos Firewall for network scanning...")
            scanner = SophosNetworkScanner(
                firewall_host=options['sophos_host'],
                firewall_port=options['sophos_port']
            )
            
            if not scanner.connect(username=options['sophos_username'], password=password):
                self.stdout.write(self.style.ERROR("Failed to connect to Sophos firewall"))
                return
            
            # Default networks for Sophos scanning
            networks = ['192.168.253.0/24', '192.168.254.0/24']
            if options['network']:
                networks = [options['network']]
            
        else:
            # Use traditional scanner
            scanner = NetworkScanner(
                timeout=options['timeout'],
                max_threads=options['threads'],
                use_sophos=False
            )
            
            if options['auto']:
                networks = scanner.get_local_networks()
                self.stdout.write(f"Auto-detected networks: {', '.join(networks)}")
            elif options['network']:
                networks = [options['network']]
            else:
                self.stdout.write(self.style.ERROR("Please specify --network or use --auto"))
                return
        
        total_devices_found = 0
        total_devices_created = 0
        total_devices_updated = 0
        
        for network in networks:
            self.stdout.write(f"Scanning network: {network}")
            devices = scanner.scan_network(network)
            
            self.stdout.write(f"Found {len(devices)} devices in {network}")
            
            for device_info in devices:
                total_devices_found += 1
                
                # Check if device already exists
                existing_device = None
                if device_info['mac_address']:
                    existing_device = NetworkDevice.objects.filter(
                        mac_address=device_info['mac_address']
                    ).first()
                
                if not existing_device:
                    existing_device = NetworkDevice.objects.filter(
                        ip_address=device_info['ip_address']
                    ).first()
                
                if existing_device:
                    if options['update_existing']:
                        # Update existing device
                        existing_device.ip_address = device_info['ip_address']
                        existing_device.mac_address = device_info['mac_address']
                        existing_device.vendor = device_info['vendor']
                        existing_device.hostname = device_info['hostname']
                        existing_device.device_type = device_info['device_type']
                        existing_device.open_ports = device_info['open_ports']
                        existing_device.last_seen = timezone.now()
                        existing_device.is_active = True
                        existing_device.save()
                        total_devices_updated += 1
                        self.stdout.write(f"Updated: {existing_device.name} ({existing_device.ip_address})")
                    else:
                        # Just update last_seen
                        existing_device.last_seen = timezone.now()
                        existing_device.is_active = True
                        existing_device.save()
                        self.stdout.write(f"Seen: {existing_device.name} ({existing_device.ip_address})")
                else:
                    # Create new device
                    device_name = device_info['hostname'] or f"Device-{device_info['ip_address'].split('.')[-1]}"
                    
                    # Ensure name is unique
                    base_name = device_name
                    counter = 1
                    while NetworkDevice.objects.filter(name=device_name).exists():
                        device_name = f"{base_name}-{counter}"
                        counter += 1
                    
                    new_device = NetworkDevice.objects.create(
                        name=device_name,
                        device_type=device_info['device_type'],
                        ip_address=device_info['ip_address'],
                        mac_address=device_info['mac_address'],
                        vendor=device_info['vendor'],
                        hostname=device_info['hostname'],
                        open_ports=device_info['open_ports'],
                        auto_discovered=True,
                        is_active=True,
                    )
                    total_devices_created += 1
                    self.stdout.write(f"Created: {new_device.name} ({new_device.ip_address}) - {new_device.get_device_type_display()}")
        
        # Mark devices as inactive if they weren't seen in this scan
        if options['update_existing']:
            recent_cutoff = timezone.now() - timezone.timedelta(hours=24)
            inactive_count = NetworkDevice.objects.filter(
                auto_discovered=True,
                last_seen__lt=recent_cutoff,
                is_active=True
            ).update(is_active=False)
            
            if inactive_count > 0:
                self.stdout.write(f"Marked {inactive_count} devices as inactive")
        
        # Summary
        self.stdout.write(self.style.SUCCESS(
            f"Scan complete! "
            f"Total found: {total_devices_found}, "
            f"Created: {total_devices_created}, "
            f"Updated: {total_devices_updated}"
        ))
