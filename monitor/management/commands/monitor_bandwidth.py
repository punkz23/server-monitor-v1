"""
Django management command to monitor network bandwidth for devices
"""

import time
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from monitor.models import NetworkDevice, DeviceBandwidthMeasurement
from monitor.services.bandwidth_monitor import BandwidthMonitor

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Monitor network bandwidth for devices'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='Monitoring interval in seconds (default: 60)'
        )
        parser.add_argument(
            '--duration',
            type=int,
            default=0,
            help='Total monitoring duration in minutes (0 for infinite, default: 0)'
        )
        parser.add_argument(
            '--device-ip',
            type=str,
            help='Monitor specific device IP only'
        )
        parser.add_argument(
            '--method',
            type=str,
            choices=['snmp', 'netstat', 'arp', 'auto'],
            default='auto',
            help='Monitoring method (default: auto)'
        )
        parser.add_argument(
            '--snmp-community',
            type=str,
            default='public',
            help='SNMP community string (default: public)'
        )
        parser.add_argument(
            '--auto',
            action='store_true',
            help='Monitor all active devices automatically (same as --method auto without --device-ip)'
        )
    
    def handle(self, *args, **options):
        interval = options['interval']
        duration = options['duration']
        device_ip = options['device_ip']
        method = options['method']
        snmp_community = options['snmp_community']
        auto_mode = options['auto']
        
        # Handle auto mode
        if auto_mode:
            device_ip = None  # Monitor all devices
            method = 'auto'
        
        monitor = BandwidthMonitor()
        monitor.snmp_community = snmp_community
        
        self.stdout.write(f"Starting bandwidth monitoring...")
        self.stdout.write(f"Interval: {interval} seconds")
        self.stdout.write(f"Method: {method}")
        self.stdout.write(f"SNMP Community: {snmp_community}")
        
        if device_ip:
            self.stdout.write(f"Target device: {device_ip}")
        elif auto_mode:
            self.stdout.write("Target: All active devices (auto mode)")
        else:
            self.stdout.write("Target: All active SNMP-enabled devices")
        
        if duration > 0:
            self.stdout.write(f"Duration: {duration} minutes")
        else:
            self.stdout.write("Duration: Infinite (Ctrl+C to stop)")
        
        start_time = timezone.now()
        end_time = start_time + timedelta(minutes=duration) if duration > 0 else None
        
        # Store previous measurements for rate calculation
        previous_measurements = {}
        
        try:
            while True:
                current_time = timezone.now()
                
                # Check if duration exceeded
                if end_time and current_time >= end_time:
                    self.stdout.write("Monitoring duration completed.")
                    break
                
                # Get devices to monitor
                if device_ip:
                    devices = NetworkDevice.objects.filter(ip_address=device_ip, enabled=True)
                else:
                    # Monitor SNMP-enabled devices that are active
                    devices = NetworkDevice.objects.filter(
                        enabled=True, 
                        is_active=True
                    ).exclude(
                        device_type__in=['MOBILE', 'UNKNOWN']  # Skip mobile and unknown devices
                    )
                
                if not devices:
                    self.stdout.write("No devices to monitor. Waiting...")
                    time.sleep(interval)
                    continue
                
                measurements_created = 0
                
                for device in devices:
                    try:
                        # Get current bandwidth data
                        bandwidth_data = monitor.monitor_device_bandwidth(
                            device.ip_address, 
                            method=method
                        )
                        
                        if bandwidth_data:
                            # Calculate rates if we have previous data
                            device_key = f"{device.ip_address}_{bandwidth_data.interface or 'default'}"
                            rates = {'bps_in': 0, 'bps_out': 0, 'pps_in': 0, 'pps_out': 0}
                            
                            if device_key in previous_measurements:
                                rates = monitor.calculate_bandwidth_rate(
                                    bandwidth_data, 
                                    previous_measurements[device_key]
                                )
                            
                            # Store measurement
                            measurement = DeviceBandwidthMeasurement.objects.create(
                                device=device,
                                interface=bandwidth_data.interface,
                                bytes_in=bandwidth_data.bytes_in,
                                bytes_out=bandwidth_data.bytes_out,
                                packets_in=bandwidth_data.packets_in,
                                packets_out=bandwidth_data.packets_out,
                                bps_in=rates['bps_in'],
                                bps_out=rates['bps_out'],
                                pps_in=rates['pps_in'],
                                pps_out=rates['pps_out'],
                                measurement_method=method
                            )
                            
                            # Store for next iteration
                            previous_measurements[device_key] = bandwidth_data
                            
                            measurements_created += 1
                            
                            # Log measurement
                            total_mbps = measurement.total_mbps
                            if total_mbps > 0.1:  # Only log if significant traffic
                                self.stdout.write(
                                    f"{device.name} ({device.ip_address}): "
                                    f"{total_mbps:.2f} Mbps "
                                    f"In: {measurement.mbps_in:.2f} Mbps "
                                    f"Out: {measurement.mbps_out:.2f} Mbps"
                                )
                        else:
                            self.stdout.write(
                                f"Failed to get bandwidth data for {device.name} ({device.ip_address})"
                            )
                            
                    except Exception as e:
                        logger.error(f"Error monitoring {device.ip_address}: {e}")
                        self.stdout.write(
                            self.style.ERROR(f"Error monitoring {device.name}: {e}")
                        )
                
                if measurements_created > 0:
                    self.stdout.write(f"Created {measurements_created} measurements")
                
                # Clean up old measurements (keep last 24 hours)
                DeviceBandwidthMeasurement.objects.filter(
                    timestamp__lt=timezone.now() - timedelta(hours=24)
                ).delete()
                
                # Wait for next interval
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.stdout.write("\nMonitoring stopped by user.")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Monitoring error: {e}"))
            logger.error(f"Bandwidth monitoring error: {e}", exc_info=True)
