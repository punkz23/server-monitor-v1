from django.core.management.base import BaseCommand
from monitor.models import Server, NetworkDevice
from django.utils import timezone
import requests
import socket
import subprocess
import logging
import os

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Automatically update server statuses for monitoring'

    def add_arguments(self, parser):
        parser.add_argument(
            '--server-ip',
            type=str,
            help='Check specific server IP only',
        )
        parser.add_argument(
            '--timeout',
            type=int,
            default=5,
            help='Connection timeout in seconds',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Verbose output',
        )

    def handle(self, *args, **options):
        timeout = options['timeout']
        verbose = options['verbose']
        server_ip = options.get('server_ip')

        self.stdout.write('🔄 Starting automated server status update...')
        
        if server_ip:
            servers = Server.objects.filter(ip_address=server_ip)
            self.stdout.write(f'🎯 Checking specific server: {server_ip}')
        else:
            servers = Server.objects.filter(enabled=True)
            self.stdout.write(f'📊 Checking {servers.count()} enabled servers...')

        updated_count = 0
        up_count = 0
        down_count = 0

        for server in servers:
            if verbose:
                self.stdout.write(f'🔍 Checking {server.name} ({server.ip_address})...')

            is_up = self.check_server_status(server.ip_address, timeout)
            old_status = server.last_status

            # Update server status
            if is_up:
                server.last_status = Server.STATUS_UP
                up_count += 1
                if verbose or old_status != Server.STATUS_UP:
                    self.stdout.write(self.style.SUCCESS(f'✅ {server.name} is UP'))
            else:
                server.last_status = Server.STATUS_DOWN
                down_count += 1
                if verbose or old_status != Server.STATUS_DOWN:
                    self.stdout.write(self.style.ERROR(f'❌ {server.name} is DOWN'))

            server.last_checked = timezone.now()
            server.save()
            updated_count += 1

        # Summary
        self.stdout.write('\n📊 Update Summary:')
        self.stdout.write(f'🔄 Servers updated: {updated_count}')
        self.stdout.write(self.style.SUCCESS(f'✅ Servers UP: {up_count}'))
        self.stdout.write(self.style.ERROR(f'❌ Servers DOWN: {down_count}'))
        
        uptime_percentage = round((up_count / updated_count * 100) if updated_count > 0 else 0, 1)
        self.stdout.write(f'📈 Uptime: {uptime_percentage}%')
        
        self.stdout.write(self.style.SUCCESS('✅ Server status update completed!'))

    def check_server_status(self, ip_address, timeout=5):
        """Check if server is up using multiple methods - prioritizing service checks"""
        
        # Method 1: HTTP request (most reliable for web servers)
        try:
            response = requests.get(f'http://{ip_address}', timeout=timeout)
            # Any HTTP response means the web server is running
            return True
        except requests.exceptions.RequestException:
            pass

        # Method 2: HTTPS request
        try:
            response = requests.get(f'https://{ip_address}', timeout=timeout, verify=False)
            return True
        except requests.exceptions.RequestException:
            pass

        # Method 3: Port check (HTTP)
        try:
            sock = socket.create_connection((ip_address, 80), timeout=timeout)
            sock.close()
            return True
        except (socket.error, socket.timeout):
            pass

        # Method 4: Port check (HTTPS)
        try:
            sock = socket.create_connection((ip_address, 443), timeout=timeout)
            sock.close()
            return True
        except (socket.error, socket.timeout):
            pass

        # Method 5: Check common NAS ports (for Synology, QNAP, etc.)
        nas_ports = [5001, 5000, 8080, 8443, 22, 21, 445]  # Synology DSM, web UI, SSH, FTP, SMB
        for port in nas_ports:
            try:
                sock = socket.create_connection((ip_address, port), timeout=timeout)
                sock.close()
                return True
            except (socket.error, socket.timeout):
                continue

        # Method 6: Ping (LAST RESORT - less reliable)
        # Only use ping if all service checks fail
        try:
            if os.name == 'nt':  # Windows
                result = subprocess.run(['ping', '-n', '1', ip_address], 
                                      capture_output=True, text=True, timeout=timeout)
            else:  # Linux/Mac
                result = subprocess.run(['ping', '-c', '1', ip_address], 
                                      capture_output=True, text=True, timeout=timeout)
            
            if result.returncode == 0:
                # Ping succeeded but all services failed - this is likely a false positive
                # Mark as DOWN since no actual services are responding
                return False
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass

        return False
