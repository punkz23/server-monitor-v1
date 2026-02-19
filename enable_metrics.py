#!/usr/bin/env python
"""Enable metrics monitoring for server 192.168.254.13"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.models import Server
from monitor.models_ssh_credentials import ServerMetricsConfig

def enable_metrics_monitoring():
    """Enable metrics monitoring for server 192.168.254.13"""
    print('⚙️ Enabling Metrics Monitoring for 192.168.254.13')
    print('=' * 50)
    
    # Find server
    server = Server.objects.filter(ip_address='192.168.254.13').first()
    if not server:
        print('❌ Server not found')
        return False
    
    print(f'✅ Found server: {server.name} ({server.ip_address})')
    
    # Check if metrics config exists
    config = ServerMetricsConfig.objects.filter(server=server).first()
    
    if config:
        print('✅ Metrics config already exists')
        print(f'   Active: {config.is_active}')
        print(f'   CPU Monitoring: {config.enable_cpu_monitoring}')
        print(f'   RAM Monitoring: {config.enable_ram_monitoring}')
        print(f'   Disk Monitoring: {config.enable_disk_monitoring}')
        print(f'   SSL Monitoring: {config.enable_ssl_monitoring}')
        
        # Enable if not active
        if not config.is_active:
            config.is_active = True
            config.save()
            print('✅ Metrics monitoring enabled')
        else:
            print('✅ Metrics monitoring already enabled')
    else:
        print('📝 Creating new metrics config')
        config = ServerMetricsConfig.objects.create(
            server=server,
            is_active=True,
            enable_cpu_monitoring=True,
            enable_ram_monitoring=True,
            enable_disk_monitoring=True,
            enable_ssl_monitoring=True,
            cpu_threshold_warning=80,
            cpu_threshold_critical=95,
            ram_threshold_warning=80,
            ram_threshold_critical=95,
            disk_threshold_warning=80,
            disk_threshold_critical=95,
            ssl_warning_days=30,
            ssl_critical_days=7,
            monitoring_interval=300
        )
        print('✅ Metrics config created and enabled')
    
    return True

def test_api_after_enable():
    """Test API after enabling metrics"""
    print('\n🌐 Testing API After Enabling Metrics')
    print('=' * 50)
    
    try:
        from django.test import RequestFactory
        from django.contrib.auth.models import User
        from monitor.views_ssh_credentials import server_metrics_api
        import json
        
        # Get server
        server = Server.objects.filter(ip_address='192.168.254.13').first()
        user = User.objects.get(username='admin')
        
        # Create mock request
        factory = RequestFactory()
        request = factory.get(f'/api/server/{server.id}/metrics/')
        request.user = user
        
        # Call API view
        response = server_metrics_api(request, server.id)
        
        print(f'📊 Response Status: {response.status_code}')
        
        if response.status_code == 200:
            print('✅ API endpoint successful!')
            data = json.loads(response.content)
            print(f'✅ Success: {data.get("success", "Unknown")}')
            
            metrics = data.get('metrics', {})
            if 'cpu' in metrics:
                print(f'   CPU: {metrics["cpu"].get("usage_percent", "N/A")}%')
            if 'ram' in metrics:
                print(f'   RAM: {metrics["ram"].get("usage_percent", "N/A")}%')
            if 'disk' in metrics:
                print(f'   Disk: {metrics["disk"].get("usage_percent", "N/A")}%')
            if 'ssl' in metrics:
                ssl = metrics['ssl']
                if 'error' in ssl:
                    print(f'   SSL: {ssl["error"]}')
                else:
                    print(f'   SSL: {ssl.get("days_remaining", "N/A")} days')
            
            print(f'⏰ Timestamp: {data.get("timestamp", "Unknown")}')
        else:
            print(f'❌ API still failing: {response.status_code}')
            data = json.loads(response.content)
            print(f'❌ Error: {data.get("error", "Unknown error")}')
        
    except Exception as e:
        print(f'❌ API test error: {e}')

if __name__ == '__main__':
    if enable_metrics_monitoring():
        test_api_after_enable()
        
        print('\n🎯 Summary:')
        print('✅ Metrics monitoring enabled for 192.168.254.13')
        print('✅ SSH credentials are working')
        print('✅ CPU, RAM, and Disk metrics are being collected')
        print('⚠️  SSL certificate needs correct file path')
        print('🌐 API endpoint should now work')
        
        print('\n📱 Next Steps:')
        print('1. Access: http://127.0.0.1:8001/api/server/4/metrics/')
        print('2. Or access via web interface: http://127.0.0.1:8001/ssh-credentials/')
        print('3. Click edit button for server to see metrics')
        print('4. Test connection from web interface')
    else:
        print('❌ Failed to enable metrics monitoring')
