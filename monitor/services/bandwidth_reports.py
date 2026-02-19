"""
Bandwidth Usage Report Generation Service

This service provides comprehensive report generation for Per-IP Bandwidth Usage
including PDF reports, CSV exports, and data summaries.
"""

import csv
import io
from datetime import datetime, timedelta
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import render_to_string
from ..models import NetworkDevice, DeviceBandwidthUsage


class BandwidthReportService:
    """Service for generating bandwidth usage reports"""
    
    def __init__(self, device=None):
        self.device = device
    
    def generate_csv_report(self, device_id, hours=24, view_type='consumers'):
        """Generate CSV report for bandwidth usage"""
        device = NetworkDevice.objects.get(id=device_id)
        
        # Get data based on view type
        if view_type == 'consumers':
            data = self._get_top_consumers_data(device, hours)
        elif view_type == 'summary':
            data = self._get_summary_data(device, hours)
        elif view_type == 'trends':
            data = self._get_trends_data(device, hours)
        else:
            data = self._get_top_consumers_data(device, hours)
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        filename = f"bandwidth_report_{device.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        
        if view_type == 'consumers':
            self._write_consumers_csv(writer, data, device, hours)
        elif view_type == 'summary':
            self._write_summary_csv(writer, data, device, hours)
        elif view_type == 'trends':
            self._write_trends_csv(writer, data, device, hours)
        
        return response
    
    def generate_pdf_report(self, device_id, hours=24, view_type='consumers'):
        """Generate PDF report for bandwidth usage"""
        device = NetworkDevice.objects.get(id=device_id)
        
        # Get data based on view type
        if view_type == 'consumers':
            data = self._get_top_consumers_data(device, hours)
        elif view_type == 'summary':
            data = self._get_summary_data(device, hours)
        elif view_type == 'trends':
            data = self._get_trends_data(device, hours)
        else:
            data = self._get_top_consumers_data(device, hours)
        
        # Render HTML template
        html_content = render_to_string('monitor/bandwidth_report.html', {
            'device': device,
            'data': data,
            'view_type': view_type,
            'hours': hours,
            'generated_at': timezone.now(),
            'title': f'Bandwidth Usage Report - {device.name}',
            'div': lambda x, y: x / y if y != 0 else 0,
            'mul': lambda x, y: x * y
        })
        
        response = HttpResponse(html_content, content_type='text/html')
        filename = f"bandwidth_report_{device.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    
    def _get_top_consumers_data(self, device, hours):
        """Get top bandwidth consumers data"""
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        consumers = DeviceBandwidthUsage.objects.filter(
            device=device,
            last_seen__gte=cutoff_time
        ).order_by('-bytes_sent')[:50]
        
        results = []
        for consumer in consumers:
            # Try to find device info
            device_info = None
            try:
                device_info = NetworkDevice.objects.get(ip_address=consumer.source_ip)
                device_name = device_info.name
                device_type = device_info.device_type
                hostname = device_info.hostname
            except NetworkDevice.DoesNotExist:
                device_name = f"Unknown ({consumer.source_ip})"
                device_type = "UNKNOWN"
                hostname = None
            
            results.append({
                'ip_address': consumer.source_ip,
                'device_name': device_name,
                'device_type': device_type,
                'hostname': hostname,
                'bytes_sent': consumer.bytes_sent,
                'bytes_received': consumer.bytes_received,
                'total_bytes': consumer.total_bytes,
                'packets_sent': consumer.packets_sent,
                'packets_received': consumer.packets_received,
                'total_packets': consumer.total_packets,
                'connections': consumer.connections,
                'protocols': consumer.protocols,
                'last_seen': consumer.last_seen,
                'first_seen': consumer.first_seen
            })
        
        return results
    
    def _get_summary_data(self, device, hours):
        """Get bandwidth summary data"""
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        queryset = DeviceBandwidthUsage.objects.filter(
            device=device,
            last_seen__gte=cutoff_time
        )
        
        from django.db.models import Sum, Count, Avg, Max
        
        summary = queryset.aggregate(
            total_bytes_sent=Sum('bytes_sent'),
            total_bytes_received=Sum('bytes_received'),
            total_connections=Count('connections'),
            unique_ips=Count('source_ip', distinct=True),
            avg_bytes_per_ip=Avg('bytes_sent'),
            max_bytes_single_ip=Max('bytes_sent')
        )
        
        # Get top protocols
        protocol_stats = {}
        for usage in queryset:
            for protocol in usage.protocols:
                if protocol not in protocol_stats:
                    protocol_stats[protocol] = 0
                protocol_stats[protocol] += usage.bytes_sent
        
        # Sort protocols by usage
        sorted_protocols = sorted(protocol_stats.items(), key=lambda x: x[1], reverse=True)
        
        # Add percentage calculation to each protocol
        protocols_with_percentage = []
        for protocol, bytes_count in sorted_protocols[:10]:
            percentage = (bytes_count / summary['total_bytes_total'] * 100) if summary['total_bytes_total'] > 0 else 0
            protocols_with_percentage.append({
                'protocol': protocol,
                'bytes_count': bytes_count,
                'percentage': round(percentage, 1)
            })
        
        return {
            'period_hours': hours,
            'total_bytes_sent': summary['total_bytes_sent'] or 0,
            'total_bytes_received': summary['total_bytes_received'] or 0,
            'total_bytes_total': (summary['total_bytes_sent'] or 0) + (summary['total_bytes_received'] or 0),
            'total_connections': summary['total_connections'] or 0,
            'unique_ips': summary['unique_ips'] or 0,
            'avg_bytes_per_ip': summary['avg_bytes_per_ip'] or 0,
            'max_bytes_single_ip': summary['max_bytes_single_ip'] or 0,
            'top_protocols': protocols_with_percentage
        }
    
    def _get_trends_data(self, device, hours):
        """Get bandwidth trends data"""
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        from django.db.models import Sum, Count
        from django.db.models.functions import TruncHour
        
        # Group by hour
        hourly_data = DeviceBandwidthUsage.objects.filter(
            device=device,
            last_seen__gte=cutoff_time
        ).annotate(
            hour=TruncHour('last_seen')
        ).values('hour').annotate(
            bytes_sent=Sum('bytes_sent'),
            bytes_received=Sum('bytes_received'),
            connections=Count('source_ip', distinct=True)
        ).order_by('hour')
        
        trends = []
        for data in hourly_data:
            trends.append({
                'hour': data['hour'],
                'bytes_sent': data['bytes_sent'] or 0,
                'bytes_received': data['bytes_received'] or 0,
                'total_bytes': (data['bytes_sent'] or 0) + (data['bytes_received'] or 0),
                'unique_ips': data['connections']
            })
        
        return trends
    
    def _write_consumers_csv(self, writer, data, device, hours):
        """Write consumers data to CSV"""
        writer.writerow([
            'IP Address', 'Device Name', 'Device Type', 'Hostname',
            'Bytes Sent', 'Bytes Received', 'Total Bytes',
            'Packets Sent', 'Packets Received', 'Total Packets',
            'Connections', 'Protocols', 'First Seen', 'Last Seen'
        ])
        
        for item in data:
            writer.writerow([
                item['ip_address'],
                item['device_name'],
                item['device_type'],
                item['hostname'] or '',
                item['bytes_sent'],
                item['bytes_received'],
                item['total_bytes'],
                item['packets_sent'],
                item['packets_received'],
                item['total_packets'],
                item['connections'],
                ', '.join(item['protocols']),
                item['first_seen'].strftime('%Y-%m-%d %H:%M:%S'),
                item['last_seen'].strftime('%Y-%m-%d %H:%M:%S')
            ])
    
    def _write_summary_csv(self, writer, data, device, hours):
        """Write summary data to CSV"""
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Report Period (hours)', data['period_hours']])
        writer.writerow(['Total Bytes Sent', data['total_bytes_sent']])
        writer.writerow(['Total Bytes Received', data['total_bytes_received']])
        writer.writerow(['Total Bytes (combined)', data['total_bytes_total']])
        writer.writerow(['Total Connections', data['total_connections']])
        writer.writerow(['Unique IP Addresses', data['unique_ips']])
        writer.writerow(['Average Bytes per IP', data['avg_bytes_per_ip']])
        writer.writerow(['Max Bytes by Single IP', data['max_bytes_single_ip']])
        
        writer.writerow([])  # Empty row
        writer.writerow(['Top Protocols', 'Bytes Transferred'])
        
        for protocol, bytes_count in data['top_protocols']:
            writer.writerow([protocol, bytes_count])
    
    def _write_trends_csv(self, writer, data, device, hours):
        """Write trends data to CSV"""
        writer.writerow(['Hour', 'Bytes Sent', 'Bytes Received', 'Total Bytes', 'Unique IPs'])
        
        for item in data:
            writer.writerow([
                item['hour'].strftime('%Y-%m-%d %H:%M:%S'),
                item['bytes_sent'],
                item['bytes_received'],
                item['total_bytes'],
                item['unique_ips']
            ])
    
    def _get_report_css(self):
        """Get CSS styling for PDF reports"""
        return """
        @page {
            size: A4;
            margin: 1cm;
        }
        
        body {
            font-family: Arial, sans-serif;
            font-size: 12px;
            line-height: 1.4;
            color: #333;
        }
        
        .header {
            text-align: center;
            border-bottom: 2px solid #0066cc;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        
        .header h1 {
            color: #0066cc;
            margin: 0;
            font-size: 24px;
        }
        
        .header .subtitle {
            color: #666;
            margin-top: 5px;
        }
        
        .section {
            margin-bottom: 30px;
        }
        
        .section h2 {
            color: #0066cc;
            border-bottom: 1px solid #ddd;
            padding-bottom: 5px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        
        th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .summary-item {
            background-color: #f9f9f9;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #0066cc;
        }
        
        .summary-item .label {
            font-weight: bold;
            color: #666;
        }
        
        .summary-item .value {
            font-size: 18px;
            color: #0066cc;
            margin-top: 5px;
        }
        
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #666;
            font-size: 10px;
        }
        
        .bytes-format {
            font-family: monospace;
        }
        """
