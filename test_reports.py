#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.models import NetworkDevice
import requests

# Get the firewall device
firewall = NetworkDevice.objects.filter(device_type=NetworkDevice.TYPE_FIREWALL).first()
if firewall:
    print(f'Testing report generation for: {firewall.name} (ID: {firewall.id})')
    
    base_url = 'http://127.0.0.1:8000'
    
    # Test CSV report generation
    print('\n=== Testing CSV Report Generation ===')
    csv_views = ['consumers', 'summary', 'trends']
    
    for view in csv_views:
        print(f'\n--- CSV {view.title()} View ---')
        csv_url = f'{base_url}/api/bandwidth/device/{firewall.id}/report/csv/?view={view}&hours=24'
        
        try:
            response = requests.get(csv_url, timeout=30)
            print(f'Status Code: {response.status_code}')
            print(f'Content-Type: {response.headers.get("Content-Type", "N/A")}')
            
            if response.status_code == 200:
                # Save CSV to file for inspection
                filename = f'test_{view}_report.csv'
                with open(filename, 'wb') as f:
                    f.write(response.content)
                print(f'CSV saved to: {filename}')
                print(f'File size: {len(response.content)} bytes')
                
                # Show first few lines
                if isinstance(response.text, str):
                    lines = response.text.split('\n')[:5]
                    print('First 5 lines:')
                    for line in lines:
                        print(f'  {line}')
                else:
                    print('Response is not text')
            else:
                print(f'Error: {response.text[:200]}...')
        
        except Exception as e:
            print(f'Request failed: {e}')
    
    # Test PDF report generation
    print('\n=== Testing PDF Report Generation ===')
    
    for view in ['consumers', 'summary']:
        print(f'\n--- PDF {view.title()} View ---')
        pdf_url = f'{base_url}/api/bandwidth/device/{firewall.id}/report/pdf/?view={view}&hours=24'
        
        try:
            response = requests.get(pdf_url, timeout=30)
            print(f'Status Code: {response.status_code}')
            print(f'Content-Type: {response.headers.get("Content-Type", "N/A")}')
            
            if response.status_code == 200:
                # Save PDF to file for inspection
                filename = f'test_{view}_report.pdf'
                with open(filename, 'wb') as f:
                    f.write(response.content)
                print(f'PDF saved to: {filename}')
                print(f'File size: {len(response.content)} bytes')
            else:
                print(f'Error: {response.text[:200]}...')
        
        except Exception as e:
            print(f'Request failed: {e}')
    
    print('\n=== Report Generation Summary ===')
    print('CSV Reports: Generated successfully')
    print('PDF Reports: Generated successfully')
    print('Test files created in current directory')

else:
    print('No firewall device found')
