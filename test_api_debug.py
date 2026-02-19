#!/usr/bin/env python
"""Test API endpoint for server metrics"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from monitor.views_ssh_credentials import server_metrics_api
from monitor.models import Server
import json

def test_api_endpoint():
    """Test API endpoint with proper authentication"""
    print('🌐 Testing API Endpoint for Server Metrics')
    print('=' * 50)
    
    try:
        # Get server
        server = Server.objects.filter(ip_address='192.168.254.13').first()
        if not server:
            print('❌ Server not found')
            return
        
        print(f'✅ Found server: {server.name} (ID: {server.id})')
        
        # Get admin user
        user = User.objects.get(username='admin')
        print(f'✅ Found user: {user.username}')
        
        # Create mock request
        factory = RequestFactory()
        request = factory.get(f'/api/server/{server.id}/metrics/')
        request.user = user
        
        print(f'📡 Making request to: /api/server/{server.id}/metrics/')
        
        # Call API view
        response = server_metrics_api(request, server.id)
        
        print(f'📊 Response Status: {response.status_code}')
        print(f'📋 Response Content-Type: {response.get("Content-Type", "Unknown")}')
        
        if response.status_code == 200:
            print('✅ API endpoint successful!')
            try:
                data = json.loads(response.content)
                print(f'✅ Success: {data.get("success", "Unknown")}')
                print(f'📊 Metrics: {json.dumps(data.get("metrics", {}), indent=2)}')
                print(f'🔄 Changes: {json.dumps(data.get("changes", {}), indent=2)}')
                print(f'⏰ Timestamp: {data.get("timestamp", "Unknown")}')
            except json.JSONDecodeError as e:
                print(f'❌ JSON decode error: {e}')
                print(f'📄 Raw response: {response.content[:500]}...')
        else:
            print(f'❌ API endpoint failed with status {response.status_code}')
            try:
                data = json.loads(response.content)
                print(f'❌ Error: {data.get("error", "Unknown error")}')
            except:
                print(f'📄 Raw response: {response.content}')
        
    except Exception as e:
        print(f'❌ API test error: {e}')
        import traceback
        traceback.print_exc()

def test_direct_api_call():
    """Test API call without Django test framework"""
    print('\n🔍 Testing Direct API Call')
    print('=' * 50)
    
    try:
        from monitor.services.metrics_monitor_service import MetricsMonitorService
        
        # Initialize service
        monitor = MetricsMonitorService()
        
        # Get server
        server = Server.objects.filter(ip_address='192.168.254.13').first()
        if not server:
            print('❌ Server not found')
            return
        
        # Load SSH credentials
        from monitor.models_ssh_credentials import SSHCredential
        credential = SSHCredential.objects.filter(server=server, is_active=True).first()
        
        if credential:
            monitor.ssh_credentials[server.ip_address] = {
                'username': credential.username,
                'password': credential.get_password(),
                'port': credential.port
            }
            print('✅ SSH credentials loaded into monitor')
        else:
            print('❌ No SSH credentials found')
            return
        
        # Test metrics collection directly
        metrics_data = monitor.get_comprehensive_metrics(server.ip_address)
        
        if 'error' in metrics_data:
            print(f'❌ Metrics error: {metrics_data["error"]}')
        else:
            print('✅ Metrics collection successful!')
            print(f'📊 Current: {json.dumps(metrics_data.get("current", {}), indent=2)}')
            print(f'🔄 Changes: {json.dumps(metrics_data.get("changes", {}), indent=2)}')
        
    except Exception as e:
        print(f'❌ Direct API test error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_api_endpoint()
    test_direct_api_call()
