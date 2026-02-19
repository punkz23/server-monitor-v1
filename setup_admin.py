#!/usr/bin/env python
"""Create or update admin user for Django login"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from django.contrib.auth.models import User

def create_admin_user():
    """Create or update admin user"""
    try:
        # Check if admin user exists
        admin_user = User.objects.filter(username='admin').first()
        
        if admin_user:
            print(f"✅ Admin user 'admin' already exists")
            print(f"   ID: {admin_user.id}")
            print(f"   Email: {admin_user.email}")
            print(f"   Staff: {admin_user.is_staff}")
            print(f"   Superuser: {admin_user.is_superuser}")
            
            # Update password to admin123
            admin_user.set_password('admin123')
            admin_user.save()
            print("✅ Password updated to 'admin123'")
        else:
            # Create admin user
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@serverwatch.local',
                password='admin123',
                first_name='Administrator',
                last_name='User'
            )
            print(f"✅ Created admin user 'admin' with password 'admin123'")
            print(f"   ID: {admin_user.id}")
            print(f"   Email: {admin_user.email}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return False

def test_login():
    """Test login functionality"""
    try:
        from django.contrib.auth import authenticate
        
        # Test authentication
        user = authenticate(username='admin', password='admin123')
        
        if user:
            print("✅ Authentication test successful")
            print(f"   User: {user.username}")
            print(f"   ID: {user.id}")
            print(f"   Is Staff: {user.is_staff}")
            print(f"   Is Superuser: {user.is_superuser}")
            return True
        else:
            print("❌ Authentication test failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing login: {e}")
        return False

if __name__ == '__main__':
    print('🔧 Django Admin User Setup')
    print('=' * 40)
    
    # Create/update admin user
    if create_admin_user():
        print()
        
        # Test login
        if test_login():
            print()
            print('🎉 Admin user is ready for login!')
            print('📱 Login URL: http://127.0.0.1:8001/login/')
            print('👤 Username: admin')
            print('🔐 Password: admin123')
        else:
            print('❌ Login test failed')
    else:
        print('❌ Failed to create admin user')
