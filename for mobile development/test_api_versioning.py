#!/usr/bin/env python3
"""
API Versioning Test Script for Django ServerWatch

This script tests API versioning functionality including:
- Version detection methods
- Version-specific endpoints
- Backward compatibility
- Header responses
- Error handling

Usage: python test_api_versioning.py --base-url http://localhost:8000
"""

import requests
import json
import argparse
import sys
from datetime import datetime

class APIVersioningTester:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        self.token = None
    
    def login(self, username='test_user_new', password='TestPass123!'):
        """Login to get authentication token"""
        login_url = f"{self.base_url}/api/auth/login/"
        data = {
            'username': username,
            'password': password
        }
        
        try:
            response = self.session.post(login_url, json=data)
            if response.status_code == 200:
                result = response.json()
                self.token = result.get('token')
                self.session.headers.update({
                    'Authorization': f'Token {self.token}'
                })
                print(f"✅ Login successful, token: {self.token[:8]}...")
                return True
            else:
                print(f"❌ Login failed: {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Login request failed: {e}")
            return False
    
    def test_version_detection_methods(self):
        """Test different version detection methods"""
        print(f"\n{'='*60}")
        print(f"Testing Version Detection Methods")
        print(f"{'='*60}")
        
        methods = [
            ('URL Path', lambda: self.test_url_versioning()),
            ('Accept Header', lambda: self.test_header_versioning()),
            ('Query Parameter', lambda: self.test_query_versioning()),
            ('Custom Header', lambda: self.test_custom_header_versioning()),
        ]
        
        results = []
        for method_name, test_func in methods:
            print(f"\n--- Testing {method_name} ---")
            try:
                success = test_func()
                results.append((method_name, success))
                print(f"{'✅' if success else '❌'} {method_name}: {'PASS' if success else 'FAIL'}")
            except Exception as e:
                print(f"❌ {method_name}: ERROR - {e}")
                results.append((method_name, False))
        
        return results
    
    def test_url_versioning(self):
        """Test URL path versioning"""
        try:
            # Test V1
            response = self.session.get(f"{self.base_url}/api/v1/mobile/dashboard/")
            if response.status_code != 200:
                return False
            
            # Check version header
            if response.headers.get('API-Version') != '1':
                return False
            
            # Test V2
            response = self.session.get(f"{self.base_url}/api/v2/mobile/dashboard/")
            if response.status_code != 200:
                return False
            
            # Check version header
            if response.headers.get('API-Version') != '2':
                return False
            
            return True
        except Exception:
            return False
    
    def test_header_versioning(self):
        """Test Accept header versioning"""
        try:
            # Test V1 with Accept header
            headers = {'Accept': 'application/vnd.api+json;version=1'}
            response = self.session.get(f"{self.base_url}/api/mobile/dashboard/", headers=headers)
            if response.status_code != 200:
                return False
            
            if response.headers.get('API-Version') != '1':
                return False
            
            # Test V2 with Accept header
            headers = {'Accept': 'application/vnd.api+json;version=2'}
            response = self.session.get(f"{self.base_url}/api/mobile/dashboard/", headers=headers)
            if response.status_code != 200:
                return False
            
            if response.headers.get('API-Version') != '2':
                return False
            
            return True
        except Exception:
            return False
    
    def test_query_versioning(self):
        """Test query parameter versioning"""
        try:
            # Test V1 with query parameter
            response = self.session.get(f"{self.base_url}/api/mobile/dashboard/?version=1")
            if response.status_code != 200:
                return False
            
            if response.headers.get('API-Version') != '1':
                return False
            
            # Test V2 with query parameter
            response = self.session.get(f"{self.base_url}/api/mobile/dashboard/?version=2")
            if response.status_code != 200:
                return False
            
            if response.headers.get('API-Version') != '2':
                return False
            
            return True
        except Exception:
            return False
    
    def test_custom_header_versioning(self):
        """Test custom header versioning"""
        try:
            # Test V1 with custom header
            headers = {'X-API-Version': '1'}
            response = self.session.get(f"{self.base_url}/api/mobile/dashboard/", headers=headers)
            if response.status_code != 200:
                return False
            
            if response.headers.get('API-Version') != '1':
                return False
            
            # Test V2 with custom header
            headers = {'X-API-Version': '2'}
            response = self.session.get(f"{self.base_url}/api/mobile/dashboard/", headers=headers)
            if response.status_code != 200:
                return False
            
            if response.headers.get('API-Version') != '2':
                return False
            
            return True
        except Exception:
            return False
    
    def test_version_specific_endpoints(self):
        """Test version-specific endpoints"""
        print(f"\n{'='*60}")
        print(f"Testing Version-Specific Endpoints")
        print(f"{'='*60}")
        
        endpoints = [
            ('V1 Dashboard', '/api/v1/mobile/dashboard/'),
            ('V2 Dashboard', '/api/v2/mobile/dashboard/'),
            ('V1 Server Status', '/api/v1/mobile/server-status/'),
            ('V2 Server Status', '/api/v2/mobile/server-status/'),
            ('V1 Alerts', '/api/v1/mobile/alerts/'),
            ('V2 Alerts', '/api/v2/mobile/alerts/'),
        ]
        
        results = []
        for endpoint_name, endpoint_url in endpoints:
            print(f"\n--- Testing {endpoint_name} ---")
            try:
                response = self.session.get(f"{self.base_url}{endpoint_url}")
                success = response.status_code == 200
                
                if success:
                    data = response.json()
                    version = response.headers.get('API-Version')
                    print(f"✅ {endpoint_name}: OK (Version {version})")
                    
                    # Check for V2 specific features
                    if 'v2' in endpoint_name.lower():
                        has_v2_features = self.check_v2_features(data)
                        print(f"   V2 Features: {'✅' if has_v2_features else '❌'}")
                else:
                    print(f"❌ {endpoint_name}: HTTP {response.status_code}")
                
                results.append((endpoint_name, success))
            except Exception as e:
                print(f"❌ {endpoint_name}: ERROR - {e}")
                results.append((endpoint_name, False))
        
        return results
    
    def check_v2_features(self, data):
        """Check if response contains V2 specific features"""
        v2_indicators = [
            'health_metrics',
            'performance_metrics',
            'trends',
            'api_version',
            'enhanced_features'
        ]
        
        return any(indicator in data for indicator in v2_indicators)
    
    def test_backward_compatibility(self):
        """Test backward compatibility"""
        print(f"\n{'='*60}")
        print(f"Testing Backward Compatibility")
        print(f"{'='*60}")
        
        # Test that V1 still works as expected
        try:
            response = self.session.get(f"{self.base_url}/api/v1/mobile/dashboard/")
            if response.status_code != 200:
                return False
            
            data = response.json()
            
            # Check V1 structure
            required_v1_fields = ['servers', 'network_devices', 'alerts', 'timestamp']
            if not all(field in data for field in required_v1_fields):
                return False
            
            print("✅ V1 structure maintained")
            
            # Test that V2 has additional features but doesn't break V1 compatibility
            response = self.session.get(f"{self.base_url}/api/v2/mobile/dashboard/")
            if response.status_code != 200:
                return False
            
            data = response.json()
            
            # V2 should have V1 fields plus additional ones
            if not all(field in data for field in required_v1_fields):
                return False
            
            # Should have V2 specific fields
            if not any(field in data for field in ['health_metrics', 'performance_metrics']):
                return False
            
            print("✅ V2 extends V1 without breaking compatibility")
            return True
            
        except Exception as e:
            print(f"❌ Backward compatibility test failed: {e}")
            return False
    
    def test_version_headers(self):
        """Test version headers in responses"""
        print(f"\n{'='*60}")
        print(f"Testing Version Headers")
        print(f"{'='*60}")
        
        try:
            # Test V1 headers
            response = self.session.get(f"{self.base_url}/api/v1/mobile/dashboard/")
            headers = response.headers
            
            required_headers = ['API-Version', 'API-Version-Status', 'API-Supported-Versions']
            missing_headers = [h for h in required_headers if h not in headers]
            
            if missing_headers:
                print(f"❌ Missing V1 headers: {missing_headers}")
                return False
            
            print(f"✅ V1 headers present: {headers.get('API-Version')}")
            
            # Test V2 headers
            response = self.session.get(f"{self.base_url}/api/v2/mobile/dashboard/")
            headers = response.headers
            
            if missing_headers:
                print(f"❌ Missing V2 headers: {missing_headers}")
                return False
            
            print(f"✅ V2 headers present: {headers.get('API-Version')}")
            
            # Test supported versions
            supported_versions = headers.get('API-Supported-Versions', '').split(',')
            if '1' not in supported_versions or '2' not in supported_versions:
                print(f"❌ Supported versions incorrect: {supported_versions}")
                return False
            
            print(f"✅ Supported versions: {supported_versions}")
            return True
            
        except Exception as e:
            print(f"❌ Version headers test failed: {e}")
            return False
    
    def test_error_handling(self):
        """Test error handling for versioning"""
        print(f"\n{'='*60}")
        print(f"Testing Error Handling")
        print(f"{'='*60}")
        
        # Test unsupported version
        try:
            response = self.session.get(f"{self.base_url}/api/mobile/dashboard/?version=99")
            if response.status_code != 400:
                print(f"❌ Unsupported version should return 400, got {response.status_code}")
                return False
            
            data = response.json()
            if 'error' not in data or 'supported_versions' not in data:
                print(f"❌ Error response format incorrect")
                return False
            
            print("✅ Unsupported version handled correctly")
            
            # Test invalid version format
            response = self.session.get(f"{self.base_url}/api/mobile/dashboard/?version=invalid")
            if response.status_code != 400:
                print(f"❌ Invalid version format should return 400, got {response.status_code}")
                return False
            
            print("✅ Invalid version format handled correctly")
            return True
            
        except Exception as e:
            print(f"❌ Error handling test failed: {e}")
            return False
    
    def test_api_info_endpoint(self):
        """Test API info endpoint"""
        print(f"\n{'='*60}")
        print(f"Testing API Info Endpoint")
        print(f"{'='*60}")
        
        try:
            response = self.session.get(f"{self.base_url}/api/info/")
            if response.status_code != 200:
                print(f"❌ API info endpoint failed: {response.status_code}")
                return False
            
            data = response.json()
            
            required_fields = ['api_name', 'version', 'supported_versions', 'versioning_strategies']
            if not all(field in data for field in required_fields):
                print(f"❌ API info missing required fields")
                return False
            
            print(f"✅ API info endpoint working")
            print(f"   API Name: {data.get('api_name')}")
            print(f"   Version: {data.get('version')}")
            print(f"   Supported Versions: {data.get('supported_versions')}")
            
            return True
            
        except Exception as e:
            print(f"❌ API info test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all versioning tests"""
        print(f"Starting API Versioning Tests at {datetime.now()}")
        print(f"Base URL: {self.base_url}")
        
        # Login first
        if not self.login():
            print("❌ Failed to login, aborting tests")
            return False
        
        # Run all test suites
        test_suites = [
            ('Version Detection Methods', self.test_version_detection_methods),
            ('Version-Specific Endpoints', self.test_version_specific_endpoints),
            ('Backward Compatibility', self.test_backward_compatibility),
            ('Version Headers', self.test_version_headers),
            ('Error Handling', self.test_error_handling),
            ('API Info Endpoint', self.test_api_info_endpoint),
        ]
        
        all_results = []
        
        for suite_name, test_func in test_suites:
            print(f"\n{'='*80}")
            print(f"Running: {suite_name}")
            print(f"{'='*80}")
            
            try:
                results = test_func()
                if isinstance(results, list):
                    all_results.extend([(f"{suite_name} - {name}", success) for name, success in results])
                else:
                    all_results.append((suite_name, results))
            except Exception as e:
                print(f"❌ {suite_name} failed with exception: {e}")
                all_results.append((suite_name, False))
        
        # Print summary
        print(f"\n{'='*80}")
        print("API VERSIONING TEST SUMMARY")
        print(f"{'='*80}")
        
        passed = sum(1 for _, success in all_results if success)
        total = len(all_results)
        
        for test_name, success in all_results:
            status = "PASS" if success else "FAIL"
            print(f"{status:4} | {test_name}")
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All API versioning tests passed!")
            return True
        else:
            print(f"❌ {total - passed} tests failed.")
            return False

def main():
    parser = argparse.ArgumentParser(description='Test Django ServerWatch API Versioning')
    parser.add_argument('--base-url', default='http://localhost:8000',
                       help='Base URL for the API (default: http://localhost:8000)')
    parser.add_argument('--test', choices=['detection', 'endpoints', 'compatibility', 'headers', 'errors', 'info'],
                       help='Run specific test suite only')
    
    args = parser.parse_args()
    
    tester = APIVersioningTester(args.base_url)
    
    if args.test == 'detection':
        success = tester.test_version_detection_methods()
    elif args.test == 'endpoints':
        success = tester.test_version_specific_endpoints()
    elif args.test == 'compatibility':
        success = tester.test_backward_compatibility()
    elif args.test == 'headers':
        success = tester.test_version_headers()
    elif args.test == 'errors':
        success = tester.test_error_handling()
    elif args.test == 'info':
        success = tester.test_api_info_endpoint()
    else:
        success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
