#!/usr/bin/env python
"""Generate exact file permissions needed for SSL certificate monitoring"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

def generate_permissions():
    print('=== SSL Certificate File Permissions Required ===')
    print('Format: IP_ADDRESS:USER:FILE_DIRECTORY')
    print('')
    
    # SSH credentials and certificate paths
    servers = {
        '192.168.254.13': {
            'username': 'w4-assistant',
            'cert_paths': [
                '/etc/letsencrypt/live/dailyoverland.com/cert.pem',
                '/etc/letsencrypt/archive/dailyoverland.com/cert23.pem',
                '/etc/letsencrypt/archive/dailyoverland.com/'
            ]
        },
        '192.168.254.50': {
            'username': 'ws3-assistant',
            'cert_paths': [
                '/etc/letsencrypt/live/id.dailyoverland.com/cert.pem',
                '/etc/letsencrypt/archive/id.dailyoverland.com/cert14.pem',
                '/etc/letsencrypt/archive/id.dailyoverland.com/'
            ]
        },
        '192.168.253.15': {
            'username': 'w1-assistant',
            'cert_paths': [
                '/etc/letsencrypt/live/ho.employee.dailyoverland.com/cert.pem',
                '/etc/letsencrypt/archive/ho.employee.dailyoverland.com/cert4.pem',
                '/etc/letsencrypt/archive/ho.employee.dailyoverland.com/'
            ]
        }
    }
    
    for ip, server_info in servers.items():
        username = server_info['username']
        cert_paths = server_info['cert_paths']
        
        print(f"# {ip} - {username}")
        for path in cert_paths:
            print(f"{ip}:{username}:{path}")
        print('')

if __name__ == '__main__':
    generate_permissions()
