#!/usr/bin/env python
"""Test Django server startup with SSH credentials"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

def test_server_startup():
    print('🔍 Testing Django Server Startup with SSH Credentials')
    print('=' * 60)
    
    try:
        # Test imports
        from monitor.urls_ssh_credentials import urlpatterns as ssh_urls
        print('✅ SSH credentials URLs imported successfully')
        
        from monitor.views_ssh_credentials import ssh_credentials_list
        print('✅ SSH credentials views imported successfully')
        
        from monitor.models import Server
        servers = Server.objects.all()[:3]
        print(f'✅ Found {Server.objects.count()} servers in database')
        
        for server in servers:
            print(f'   📡 {server.name} ({server.ip_address})')
        
        print('\n🎉 All imports successful! Server should start without errors.')
        print('\n🌐 Access URLs:')
        print('   Main Dashboard: http://localhost:8000/')
        print('   Monitoring: http://localhost:8000/monitoring/')
        print('   SSH Credentials: http://localhost:8000/ssh-credentials/')
        print('   API Endpoints: http://localhost:8000/api/')
        
        return True
        
    except Exception as e:
        print(f'❌ Error during startup test: {e}')
        return False

if __name__ == '__main__':
    success = test_server_startup()
    if success:
        print('\n✅ Ready to start Django server!')
        print('   Run: python manage.py runserver 0.0.0.0:8000')
    else:
        print('\n❌ Fix errors before starting server')
