#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.models import NetworkDevice
import requests
import json

# Get the firewall device
firewall = NetworkDevice.objects.filter(device_type=NetworkDevice.TYPE_FIREWALL).first()
if firewall:
    print(f'Testing API endpoint for: {firewall.name} (ID: {firewall.id})')
    
    # Test the API endpoint directly
    api_url = f'http://127.0.0.1:8000/api/bandwidth/device/{firewall.id}/ip/'
    
    print(f'\nTesting API endpoint: {api_url}')
    
    try:
        # Test different parameters
        test_params = [
            {},  # Default
            {'hours': 24, 'limit': 10},  # Custom hours and limit
            {'view': 'summary'},  # Summary view
            {'view': 'trends'},  # Trends view
            {'view': 'range', 'ip_range': '192.168.253.0/24'},  # IP range view
        ]
        
        for i, params in enumerate(test_params, 1):
            print(f'\n--- Test {i} ---')
            print(f'Parameters: {params}')
            
            response = requests.get(api_url, params=params, timeout=10)
            
            print(f'Status Code: {response.status_code}')
            print(f'Content-Type: {response.headers.get("Content-Type", "N/A")}')
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f'Response keys: {list(data.keys())}')
                    
                    if 'data' in data:
                        data_list = data['data']
                        print(f'Data items: {len(data_list)}')
                        
                        if isinstance(data_list, list) and data_list:
                            print('Sample data item:')
                            sample = data_list[0]
                            for key, value in sample.items():
                                print(f'  {key}: {value}')
                        elif isinstance(data_list, dict):
                            print('Data is a dictionary:')
                            for key, value in data_list.items():
                                print(f'  {key}: {value}')
                        else:
                            print('No data items returned or data is not a list/dict')
                    
                    if 'view_type' in data:
                        print(f'View Type: {data["view_type"]}')
                    
                    if 'time_range_hours' in data:
                        print(f'Time Range: {data["time_range_hours"]} hours')
                    
                except json.JSONDecodeError as e:
                    print(f'Failed to decode JSON: {e}')
                    print(f'Response content: {response.text[:500]}...')
            else:
                print(f'Error response: {response.text[:500]}...')
    
    except requests.exceptions.RequestException as e:
        print(f'Request failed: {e}')
    
    print(f'\n=== Testing bandwidth summary API ===')
    summary_url = 'http://127.0.0.1:8000/api/bandwidth/summary/'
    
    try:
        response = requests.get(summary_url, timeout=10)
        print(f'Summary API Status: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            print(f'Summary keys: {list(data.keys())}')
            
            if 'summary' in data:
                summary = data['summary']
                print(f'Total devices: {summary.get("total_devices", 0)}')
                print(f'Total bandwidth: {summary.get("total_bandwidth_mbps", 0)} Mbps')
                print(f'Active devices: {summary.get("active_devices", 0)}')
        
    except Exception as e:
        print(f'Summary API error: {e}')

else:
    print('No firewall device found')
