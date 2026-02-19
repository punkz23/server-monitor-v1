#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.services.bandwidth_reports import BandwidthReportService
from monitor.models import NetworkDevice

# Get the firewall device
firewall = NetworkDevice.objects.filter(device_type=NetworkDevice.TYPE_FIREWALL).first()
if firewall:
    print(f'Testing PDF report for: {firewall.name} (ID: {firewall.id})')
    
    service = BandwidthReportService()
    try:
        response = service.generate_pdf_report(firewall.id, 24, 'consumers')
        print('PDF report generated successfully')
        print(f'Content-Type: {response.headers.get("Content-Type", "N/A")}')
        print(f'Content-Disposition: {response.headers.get("Content-Disposition", "N/A")}')
        
        # Save to file
        filename = 'debug_pdf_report.html'
        with open(filename, 'w', encoding='utf-8') as f:
            if isinstance(response.content, str):
                f.write(response.content)
            else:
                f.write(response.content.decode('utf-8'))
        print(f'HTML report saved to: {filename}')
        
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

else:
    print('No firewall device found')
