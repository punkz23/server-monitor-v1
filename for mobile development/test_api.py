#!/usr/bin/env python3
"""
Test script for Django REST Framework API endpoints
Usage: python test_api.py --token YOUR_TOKEN --base-url http://localhost:8000
"""

import requests
import json
import argparse
import sys
from datetime import datetime

class APITester:
    def __init__(self, base_url, token=None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
        if token:
            self.session.headers.update({
                'Authorization': f'Token {token}',
                'Content-Type': 'application/json'
            })
        else:
            self.session.headers.update({
                'Content-Type': 'application/json'
            })
    
    def test_endpoint(self, endpoint, description):
        """Test a single API endpoint"""
        url = f"{self.base_url}{endpoint}"
        print(f"\n{'='*60}")
        print(f"Testing: {description}")
        print(f"URL: {url}")
        print(f"{'='*60}")
        
        try:
            response = self.session.get(url)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
                return True
            else:
                print(f"Error Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return False
    
    def test_post_endpoint(self, endpoint, data, description):
        """Test a POST API endpoint"""
        url = f"{self.base_url}{endpoint}"
        print(f"\n{'='*60}")
        print(f"Testing POST: {description}")
        print(f"URL: {url}")
        print(f"Data: {json.dumps(data, indent=2)}")
        print(f"{'='*60}")
        
        try:
            response = self.session.post(url, json=data)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            return response.status_code in [200, 201]
            
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all API tests"""
        print(f"Starting API Tests at {datetime.now()}")
        print(f"Base URL: {self.base_url}")
        
        tests = [
            # Mobile API tests
            ('/api/mobile/dashboard/', 'Mobile Dashboard Summary'),
            ('/api/mobile/server-status/', 'Mobile Server Status'),
            ('/api/mobile/network-devices/', 'Mobile Network Devices'),
            ('/api/mobile/alerts/', 'Mobile Alerts'),
            
            # Standard REST API tests
            ('/api/servers/', 'Servers List'),
            ('/api/network-devices/', 'Network Devices List'),
            ('/api/alerts/', 'Alerts List'),
            ('/api/isp-connections/', 'ISP Connections List'),
            ('/api/cctv-devices/', 'CCTV Devices List'),
        ]
        
        results = []
        for endpoint, description in tests:
            success = self.test_endpoint(endpoint, description)
            results.append((endpoint, description, success))
        
        # Test agent ingestion
        agent_data = {
            "server_id": 1,
            "cpu": {"percent": 45.2},
            "memory": {"percent": 67.8},
            "load": {"1": 1.2, "5": 1.1, "15": 0.9}
        }
        agent_success = self.test_post_endpoint(
            '/api/mobile/agent/ingest/', 
            agent_data, 
            'Mobile Agent Ingestion'
        )
        results.append(('/api/mobile/agent/ingest/', 'Mobile Agent Ingestion', agent_success))
        
        # Print summary
        print(f"\n{'='*60}")
        print("TEST SUMMARY")
        print(f"{'='*60}")
        
        passed = sum(1 for _, _, success in results if success)
        total = len(results)
        
        for endpoint, description, success in results:
            status = "PASS" if success else "FAIL"
            print(f"{status:4} | {description}")
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("All tests passed! 🎉")
            return True
        else:
            print(f"{total - passed} tests failed.")
            return False

def main():
    parser = argparse.ArgumentParser(description='Test Django REST Framework API')
    parser.add_argument('--base-url', default='http://localhost:8000',
                       help='Base URL for the API (default: http://localhost:8000)')
    parser.add_argument('--token', help='Authentication token')
    parser.add_argument('--endpoint', help='Test specific endpoint only')
    
    args = parser.parse_args()
    
    tester = APITester(args.base_url, args.token)
    
    if args.endpoint:
        success = tester.test_endpoint(args.endpoint, f"Specific endpoint: {args.endpoint}")
        sys.exit(0 if success else 1)
    else:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
