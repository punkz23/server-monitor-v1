#!/usr/bin/env python
"""Generate clean file permissions list for SSL certificate monitoring"""

def generate_clean_permissions():
    print('=== SSL Certificate File Permissions Required ===')
    print('Format: IP_ADDRESS:USER:FILE_DIRECTORY')
    print('')
    
    permissions = [
        # 192.168.254.13 - w4-assistant
        '192.168.254.13:w4-assistant:/etc/letsencrypt/live/dailyoverland.com/cert.pem',
        '192.168.254.13:w4-assistant:/etc/letsencrypt/archive/dailyoverland.com/cert23.pem',
        '192.168.254.13:w4-assistant:/etc/letsencrypt/archive/dailyoverland.com/',
        
        # 192.168.254.50 - ws3-assistant  
        '192.168.254.50:ws3-assistant:/etc/letsencrypt/live/id.dailyoverland.com/cert.pem',
        '192.168.254.50:ws3-assistant:/etc/letsencrypt/archive/id.dailyoverland.com/cert14.pem',
        '192.168.254.50:ws3-assistant:/etc/letsencrypt/archive/id.dailyoverland.com/',
        
        # 192.168.253.15 - w1-assistant
        '192.168.253.15:w1-assistant:/etc/letsencrypt/live/ho.employee.dailyoverland.com/cert.pem',
        '192.168.253.15:w1-assistant:/etc/letsencrypt/archive/ho.employee.dailyoverland.com/cert4.pem',
        '192.168.253.15:w1-assistant:/etc/letsencrypt/archive/ho.employee.dailyoverland.com/'
    ]
    
    for permission in permissions:
        print(permission)

if __name__ == '__main__':
    generate_clean_permissions()
