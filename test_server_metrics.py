#!/usr/bin/env python
"""Test SSH credentials and metrics collection for specific server"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.models import Server
from monitor.models_ssh_credentials import SSHCredential
from monitor.services.metrics_monitor_service import MetricsMonitorService

def test_ssh_credentials():
    """Test SSH credentials for server 192.168.254.13"""
    print('🔍 Testing SSH Credentials for 192.168.254.13')
    print('=' * 50)
    
    # Find server
    server = Server.objects.filter(ip_address='192.168.254.13').first()
    if not server:
        print('❌ Server 192.168.254.13 not found in database')
        return False
    
    print(f'✅ Found server: {server.name} ({server.ip_address})')
    
    # Find SSH credentials
    credential = SSHCredential.objects.filter(server=server, is_active=True).first()
    if not credential:
        print('❌ No active SSH credentials found for this server')
        return False
    
    print(f'✅ Found SSH credentials:')
    print(f'   Username: {credential.username}')
    print(f'   Port: {credential.port}')
    print(f'   Active: {credential.is_active}')
    
    # Test connection
    print('\n🔌 Testing SSH connection...')
    try:
        success, message = credential.test_connection()
        if success:
            print('✅ SSH connection successful!')
        else:
            print(f'❌ SSH connection failed: {message}')
            return False
    except Exception as e:
        print(f'❌ SSH connection error: {e}')
        return False
    
    return True

def test_metrics_collection():
    """Test metrics collection"""
    print('\n📊 Testing Metrics Collection')
    print('=' * 50)
    
    # Initialize metrics service
    monitor = MetricsMonitorService()
    
    # Load credentials for server
    monitor.load_ssh_credentials('192.168.254.13')
    
    # Check if credentials loaded
    if '192.168.254.13' not in monitor.ssh_credentials:
        print('❌ SSH credentials not loaded into metrics service')
        return False
    
    print('✅ SSH credentials loaded into metrics service')
    
    # Test metrics collection
    print('\n📈 Collecting metrics...')
    try:
        metrics_data = monitor.get_comprehensive_metrics('192.168.254.13')
        
        if 'error' in metrics_data:
            print(f'❌ Metrics collection failed: {metrics_data["error"]}')
            return False
        
        print('✅ Metrics collection successful!')
        
        # Display metrics
        current_metrics = metrics_data.get('current', {})
        
        print('\n📊 Current Metrics:')
        if 'cpu' in current_metrics:
            cpu = current_metrics['cpu']
            print(f'   CPU Usage: {cpu.get("usage_percent", "N/A")}%')
            print(f'   CPU Status: {cpu.get("status", "N/A")}')
        
        if 'ram' in current_metrics:
            ram = current_metrics['ram']
            print(f'   RAM Usage: {ram.get("usage_percent", "N/A")}%')
            print(f'   RAM Status: {ram.get("status", "N/A")}')
        
        if 'disk' in current_metrics:
            disk = current_metrics['disk']
            print(f'   Disk Usage: {disk.get("usage_percent", "N/A")}%')
            print(f'   Disk Status: {disk.get("status", "N/A")}')
        
        if 'ssl' in current_metrics:
            ssl = current_metrics['ssl']
            print(f'   SSL Days Remaining: {ssl.get("days_remaining", "N/A")}')
            print(f'   SSL Status: {ssl.get("status", "N/A")}')
        
        return True
        
    except Exception as e:
        print(f'❌ Metrics collection error: {e}')
        return False

def test_api_endpoint():
    """Test API endpoint for server metrics"""
    print('\n🌐 Testing API Endpoint')
    print('=' * 50)
    
    try:
        from monitor.views_ssh_credentials import server_metrics_api
        from django.test import RequestFactory
        from django.contrib.auth.models import User
        
        # Create mock request
        factory = RequestFactory()
        user = User.objects.get(username='admin')
        
        # Find server
        server = Server.objects.filter(ip_address='192.168.254.13').first()
        if not server:
            print('❌ Server not found for API test')
            return False
        
        request = factory.get(f'/api/server/{server.id}/metrics/')
        request.user = user
        
        # Call API view
        response = server_metrics_api(request, server.id)
        
        if response.status_code == 200:
            print('✅ API endpoint working!')
            import json
            data = json.loads(response.content)
            
            if data.get('success'):
                print('✅ API returned success!')
                metrics = data.get('metrics', {})
                print(f'   CPU: {metrics.get("cpu", {}).get("usage_percent", "N/A")}%')
                print(f'   RAM: {metrics.get("ram", {}).get("usage_percent", "N/A")}%')
                print(f'   Disk: {metrics.get("disk", {}).get("usage_percent", "N/A")}%')
                print(f'   SSL: {metrics.get("ssl", {}).get("days_remaining", "N/A")} days')
            else:
                print(f'❌ API returned error: {data.get("error", "Unknown error")}')
        else:
            print(f'❌ API endpoint failed with status {response.status_code}')
            
    except Exception as e:
        print(f'❌ API test error: {e}')
        return False
    
    return True

if __name__ == '__main__':
    print('🔧 SSH Credentials and Metrics Test')
    print('=' * 60)
    
    # Test SSH credentials
    if test_ssh_credentials():
        # Test metrics collection
        if test_metrics_collection():
            # Test API endpoint
            test_api_endpoint()
        else:
            print('\n❌ Metrics collection failed - check SSH connection and permissions')
    else:
        print('\n❌ SSH credentials test failed - check credentials and server connectivity')
    
    print('\n🎯 Next Steps:')
    print('1. If SSH connection works but metrics fail, check server commands')
    print('2. If API fails, check authentication and permissions')
    print('3. Access SSH credentials page to verify configuration')
    print('4. Test connection from web interface')
