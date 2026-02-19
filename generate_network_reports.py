#!/usr/bin/env python
"""Report generation script for network devices categorized by network and ordered by device type"""

import os
import sys
import django
import csv
from io import StringIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.models import NetworkDevice


class NetworkDeviceReportGenerator:
    """Generate reports for network devices categorized by network and ordered by device type"""
    
    def __init__(self):
        self.devices = NetworkDevice.objects.all().select_related()
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue
        )
    
    def get_devices_by_network_and_type(self):
        """Get devices grouped by network and ordered by device type"""
        devices_dict = {}
        
        # Group devices by network
        for device in self.devices:
            network = device.network or 'Unknown Network'
            if network not in devices_dict:
                devices_dict[network] = []
            devices_dict[network].append(device)
        
        # Sort each network's devices by device type, then name
        for network in devices_dict:
            devices_dict[network].sort(key=lambda x: (x.device_type, x.name))
        
        # Sort networks alphabetically
        return dict(sorted(devices_dict.items()))
    
    def generate_csv_report(self):
        """Generate CSV report"""
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Network', 'Device Name', 'Device Type', 'IP Address', 'MAC Address', 'Vendor', 'Hostname', 'Status', 'First Seen', 'Last Seen'])
        
        # Group devices by network and type
        devices_by_network = self.get_devices_by_network_and_type()
        
        for network, devices in devices_by_network.items():
            for device in devices:
                writer.writerow([
                    network,
                    device.name,
                    device.get_device_type_display(),
                    device.ip_address,
                    device.mac_address or '',
                    device.vendor or '',
                    device.hostname or '',
                    'Active' if device.is_active else 'Inactive',
                    device.first_seen.strftime('%Y-%m-%d %H:%M') if device.first_seen else '',
                    device.last_seen.strftime('%Y-%m-%d %H:%M') if device.last_seen else ''
                ])
        
        return output.getvalue()
    
    def generate_pdf_report(self, filename='network_devices_report.pdf'):
        """Generate PDF report"""
        doc = SimpleDocTemplate(filename, pagesize=A4)
        story = []
        
        # Title
        title = Paragraph("Network Devices Report", self.title_style)
        story.append(title)
        
        # Report generation time
        timestamp = Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.styles['Normal'])
        story.append(timestamp)
        story.append(Spacer(1, 20))
        
        # Summary statistics
        devices_by_network = self.get_devices_by_network_and_type()
        total_devices = sum(len(devices) for devices in devices_by_network.values())
        
        summary_data = [
            ['Total Networks:', str(len(devices_by_network))],
            ['Total Devices:', str(total_devices)],
        ]
        
        # Device type summary
        device_type_counts = {}
        for devices in devices_by_network.values():
            for device in devices:
                device_type = device.get_device_type_display()
                device_type_counts[device_type] = device_type_counts.get(device_type, 0) + 1
        
        for device_type, count in sorted(device_type_counts.items()):
            summary_data.append([f'{device_type}:', str(count)])
        
        summary_table = Table(summary_data, colWidths=[2*inch, 1*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(Paragraph("Summary Statistics", self.heading_style))
        story.append(summary_table)
        story.append(Spacer(1, 30))
        
        # Detailed devices by network
        for network, devices in devices_by_network.items():
            # Network heading
            story.append(Paragraph(f"Network: {network}", self.heading_style))
            story.append(Spacer(1, 12))
            
            # Device table
            table_data = [['Device Name', 'Type', 'IP Address', 'MAC Address', 'Vendor', 'Status']]
            
            for device in devices:
                table_data.append([
                    device.name,
                    device.get_device_type_display(),
                    device.ip_address,
                    device.mac_address or 'N/A',
                    device.vendor or 'N/A',
                    'Active' if device.is_active else 'Inactive'
                ])
            
            # Create table
            table = Table(table_data, colWidths=[1.8*inch, 1.2*inch, 1.2*inch, 1.3*inch, 1.2*inch, 0.8*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
            ]))
            
            story.append(table)
            story.append(Spacer(1, 20))
        
        # Build PDF
        doc.build(story)
        return filename
    
    def save_csv_report(self, filename='network_devices_report.csv'):
        """Save CSV report to file"""
        csv_content = self.generate_csv_report()
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            f.write(csv_content)
        return filename
    
    def generate_reports(self, csv_filename='network_devices_report.csv', pdf_filename='network_devices_report.pdf'):
        """Generate both CSV and PDF reports"""
        csv_file = self.save_csv_report(csv_filename)
        pdf_file = self.generate_pdf_report(pdf_filename)
        
        return {
            'csv_file': csv_file,
            'pdf_file': pdf_file,
            'total_networks': len(self.get_devices_by_network_and_type()),
            'total_devices': self.devices.count()
        }


def main():
    """Main function to generate reports"""
    print("Network Devices Report Generator")
    print("=" * 50)
    
    try:
        generator = NetworkDeviceReportGenerator()
        results = generator.generate_reports()
        
        print(f"✓ CSV report generated: {results['csv_file']}")
        print(f"✓ PDF report generated: {results['pdf_file']}")
        print(f"✓ Total networks: {results['total_networks']}")
        print(f"✓ Total devices: {results['total_devices']}")
        print("\nReports completed successfully!")
        
    except Exception as e:
        print(f"✗ Error generating reports: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
