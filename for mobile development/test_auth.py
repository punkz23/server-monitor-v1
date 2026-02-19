#!/usr/bin/env python3
"""
Authentication Test Script for Django ServerWatch Mobile API

This script tests all authentication endpoints and demonstrates proper token usage.
Usage: python test_auth.py --base-url http://localhost:8000
"""

import requests
import json
import argparse
import sys
from datetime import datetime

class AuthTester:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        self.token = None
        self.user_data = None
    
    def register_user(self, username, password, email=None):
        """Test user registration"""
        print(f"\n{'='*60}")
        print(f"Testing User Registration")
        print(f"{'='*60}")
        
        data = {
            'username': username,
            'password': password
        }
        
        if email:
            data['email'] = email
        
        url = f"{self.base_url}/api/auth/register/"
        print(f"POST {url}")
        print(f"Data: {json.dumps(data, indent=2)}")
        
        try:
            response = self.session.post(url, json=data)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 201:
                result = response.json()
                print(f"✅ Registration successful!")
                print(f"Response: {json.dumps(result, indent=2)}")
                self.token = result.get('token')
                self.user_data = result
                return True
            else:
                print(f"❌ Registration failed!")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            return False
    
    def login_user(self, username, password):
        """Test user login"""
        print(f"\n{'='*60}")
        print(f"Testing User Login")
        print(f"{'='*60}")
        
        data = {
            'username': username,
            'password': password
        }
        
        url = f"{self.base_url}/api/auth/login/"
        print(f"POST {url}")
        print(f"Data: {json.dumps(data, indent=2)}")
        
        try:
            response = self.session.post(url, json=data)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Login successful!")
                print(f"Response: {json.dumps(result, indent=2)}")
                self.token = result.get('token')
                self.user_data = result
                self.session.headers.update({
                    'Authorization': f'Token {self.token}'
                })
                return True
            else:
                print(f"❌ Login failed!")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            return False
    
    def get_token_info(self):
        """Test getting token information"""
        print(f"\n{'='*60}")
        print(f"Testing Token Info")
        print(f"{'='*60}")
        
        if not self.token:
            print("❌ No token available. Please login first.")
            return False
        
        url = f"{self.base_url}/api/auth/token/info/"
        print(f"GET {url}")
        print(f"Authorization: Token {self.token[:8]}...")
        
        try:
            response = self.session.get(url)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Token info retrieved!")
                print(f"Response: {json.dumps(result, indent=2)}")
                return True
            else:
                print(f"❌ Failed to get token info!")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            return False
    
    def get_profile(self):
        """Test getting user profile"""
        print(f"\n{'='*60}")
        print(f"Testing User Profile")
        print(f"{'='*60}")
        
        if not self.token:
            print("❌ No token available. Please login first.")
            return False
        
        url = f"{self.base_url}/api/auth/profile/"
        print(f"GET {url}")
        print(f"Authorization: Token {self.token[:8]}...")
        
        try:
            response = self.session.get(url)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Profile retrieved!")
                print(f"Response: {json.dumps(result, indent=2)}")
                return True
            else:
                print(f"❌ Failed to get profile!")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            return False
    
    def refresh_token(self):
        """Test token refresh"""
        print(f"\n{'='*60}")
        print(f"Testing Token Refresh")
        print(f"{'='*60}")
        
        if not self.token:
            print("❌ No token available. Please login first.")
            return False
        
        old_token = self.token
        url = f"{self.base_url}/api/auth/token/refresh/"
        print(f"POST {url}")
        print(f"Old Token: {old_token[:8]}...")
        
        try:
            response = self.session.post(url)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Token refreshed!")
                print(f"Response: {json.dumps(result, indent=2)}")
                self.token = result.get('token')
                self.session.headers.update({
                    'Authorization': f'Token {self.token}'
                })
                print(f"New Token: {self.token[:8]}...")
                return True
            else:
                print(f"❌ Failed to refresh token!")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            return False
    
    def test_protected_endpoint(self):
        """Test accessing a protected endpoint"""
        print(f"\n{'='*60}")
        print(f"Testing Protected Endpoint")
        print(f"{'='*60}")
        
        if not self.token:
            print("❌ No token available. Please login first.")
            return False
        
        url = f"{self.base_url}/api/mobile/dashboard/"
        print(f"GET {url}")
        print(f"Authorization: Token {self.token[:8]}...")
        
        try:
            response = self.session.get(url)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Protected endpoint accessed!")
                print(f"Response: {json.dumps(result, indent=2)}")
                return True
            else:
                print(f"❌ Failed to access protected endpoint!")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            return False
    
    def logout_user(self):
        """Test user logout"""
        print(f"\n{'='*60}")
        print(f"Testing User Logout")
        print(f"{'='*60}")
        
        if not self.token:
            print("❌ No token available. Please login first.")
            return False
        
        url = f"{self.base_url}/api/auth/logout/"
        print(f"POST {url}")
        print(f"Authorization: Token {self.token[:8]}...")
        
        try:
            response = self.session.post(url)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Logout successful!")
                print(f"Response: {json.dumps(result, indent=2)}")
                self.token = None
                self.session.headers.pop('Authorization', None)
                return True
            else:
                print(f"❌ Logout failed!")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            return False
    
    def test_invalid_token(self):
        """Test accessing with invalid token"""
        print(f"\n{'='*60}")
        print(f"Testing Invalid Token")
        print(f"{'='*60}")
        
        url = f"{self.base_url}/api/mobile/dashboard/"
        print(f"GET {url}")
        print(f"Authorization: Token invalid_token_123")
        
        try:
            # Create a new session with invalid token
            temp_session = requests.Session()
            temp_session.headers.update({
                'Content-Type': 'application/json',
                'Authorization': 'Token invalid_token_123'
            })
            
            response = temp_session.get(url)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 401:
                print(f"✅ Invalid token properly rejected!")
                print(f"Response: {response.text}")
                return True
            else:
                print(f"❌ Invalid token was not rejected!")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            return False
    
    def run_full_test(self):
        """Run complete authentication test suite"""
        print(f"Starting Authentication Tests at {datetime.now()}")
        print(f"Base URL: {self.base_url}")
        
        # Test data
        test_username = f"testuser_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        test_password = "TestPass123!"
        test_email = f"{test_username}@example.com"
        
        tests = []
        
        # Test 1: Register new user
        success = self.register_user(test_username, test_password, test_email)
        tests.append(('User Registration', success))
        
        # Test 2: Get token info
        success = self.get_token_info()
        tests.append(('Get Token Info', success))
        
        # Test 3: Get user profile
        success = self.get_profile()
        tests.append(('Get User Profile', success))
        
        # Test 4: Access protected endpoint
        success = self.test_protected_endpoint()
        tests.append(('Access Protected Endpoint', success))
        
        # Test 5: Refresh token
        success = self.refresh_token()
        tests.append(('Token Refresh', success))
        
        # Test 6: Logout
        success = self.logout_user()
        tests.append(('User Logout', success))
        
        # Test 7: Try to access after logout
        success = not self.test_protected_endpoint()  # Should fail
        tests.append(('Access After Logout (should fail)', success))
        
        # Test 8: Login again
        success = self.login_user(test_username, test_password)
        tests.append(('Login Again', success))
        
        # Test 9: Test invalid token
        success = self.test_invalid_token()
        tests.append(('Invalid Token Rejection', success))
        
        # Test 10: Final logout
        success = self.logout_user()
        tests.append(('Final Logout', success))
        
        # Print summary
        print(f"\n{'='*60}")
        print("AUTHENTICATION TEST SUMMARY")
        print(f"{'='*60}")
        
        passed = sum(1 for _, success in tests if success)
        total = len(tests)
        
        for test_name, success in tests:
            status = "PASS" if success else "FAIL"
            print(f"{status:4} | {test_name}")
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All authentication tests passed!")
            return True
        else:
            print(f"❌ {total - passed} tests failed.")
            return False

def main():
    parser = argparse.ArgumentParser(description='Test Django ServerWatch Authentication API')
    parser.add_argument('--base-url', default='http://localhost:8000',
                       help='Base URL for the API (default: http://localhost:8000)')
    parser.add_argument('--test', choices=['register', 'login', 'profile', 'token', 'refresh', 'logout', 'protected'],
                       help='Run specific test only')
    
    args = parser.parse_args()
    
    tester = AuthTester(args.base_url)
    
    if args.test == 'register':
        username = input("Enter username: ")
        password = input("Enter password: ")
        email = input("Enter email (optional): ") or None
        success = tester.register_user(username, password, email)
    elif args.test == 'login':
        username = input("Enter username: ")
        password = input("Enter password: ")
        success = tester.login_user(username, password)
    elif args.test == 'profile':
        token = input("Enter auth token: ")
        tester.token = token
        tester.session.headers.update({'Authorization': f'Token {token}'})
        success = tester.get_profile()
    elif args.test == 'token':
        token = input("Enter auth token: ")
        tester.token = token
        tester.session.headers.update({'Authorization': f'Token {token}'})
        success = tester.get_token_info()
    elif args.test == 'refresh':
        token = input("Enter auth token: ")
        tester.token = token
        tester.session.headers.update({'Authorization': f'Token {token}'})
        success = tester.refresh_token()
    elif args.test == 'logout':
        token = input("Enter auth token: ")
        tester.token = token
        tester.session.headers.update({'Authorization': f'Token {token}'})
        success = tester.logout_user()
    elif args.test == 'protected':
        token = input("Enter auth token: ")
        tester.token = token
        tester.session.headers.update({'Authorization': f'Token {token}'})
        success = tester.test_protected_endpoint()
    else:
        success = tester.run_full_test()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
