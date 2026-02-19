#!/usr/bin/env python3
"""
Test ServerWatch Agent Deployment
Test script to verify agent functionality
"""

import requests
import json
import time
import sys

class AgentTester:
    def __init__(self, server_url="http://localhost:8000", token="test-token"):
        self.server_url = server_url
        self.token = token
        self.server_id = "test-server-12345"
    
    def test_heartbeat(self):
        """Test heartbeat endpoint"""
        print("🔍 Testing heartbeat endpoint...")
        
        payload = {
            "server_id": self.server_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "online",
            "agent_version": "1.0.0"
        }
        
        try:
            response = requests.post(
                f"{self.server_url}/api/agent/heartbeat/",
                json=payload,
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Heartbeat test successful")
                print(f"   Response: {response.json()}")
                return True
            else:
                print(f"❌ Heartbeat test failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Heartbeat test error: {e}")
            return False
    
    def test_metrics(self):
        """Test metrics endpoint"""
        print("\n🔍 Testing metrics endpoint...")
        
        payload = {
            "server_id": self.server_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "cpu": {
                "percent": 45.2,
                "count": 4,
                "load_1m": 1.2,
                "load_5m": 1.1,
                "load_15m": 0.9
            },
            "memory": {
                "total": 8589934592,  # 8GB
                "used": 4294967296,   # 4GB
                "percent": 50.0
            },
            "disk": {
                "total": 107374182400,  # 100GB
                "used": 53687091200,    # 50GB
                "percent": 50.0
            },
            "network": {
                "bytes_sent": 1000000,
                "bytes_recv": 2000000,
                "packets_sent": 1000,
                "packets_recv": 2000
            },
            "system": {
                "uptime_seconds": 86400,
                "process_count": 150,
                "hostname": "test-server"
            }
        }
        
        try:
            response = requests.post(
                f"{self.server_url}/api/agent/metrics/",
                json=payload,
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Metrics test successful")
                print(f"   Response: {response.json()}")
                return True
            else:
                print(f"❌ Metrics test failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Metrics test error: {e}")
            return False
    
    def test_status(self):
        """Test agent status endpoint"""
        print("\n🔍 Testing agent status endpoint...")
        
        try:
            response = requests.get(
                f"{self.server_url}/api/agent/status/",
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Agent status test successful")
                data = response.json()
                print(f"   Total servers: {data['total_servers']}")
                print(f"   Online agents: {data['online_agents']}")
                return True
            else:
                print(f"❌ Agent status test failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Agent status test error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting ServerWatch Agent Tests")
        print("=" * 50)
        
        results = []
        results.append(self.test_heartbeat())
        results.append(self.test_metrics())
        results.append(self.test_status())
        
        print("\n" + "=" * 50)
        print("📊 Test Results Summary:")
        passed = sum(results)
        total = len(results)
        
        if passed == total:
            print(f"✅ All tests passed! ({passed}/{total})")
            print("\n🎉 Agent deployment is working correctly!")
        else:
            print(f"❌ Some tests failed ({passed}/{total})")
            print("\n🔧 Check the server logs for more details")
        
        return passed == total

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Test ServerWatch Agent')
    parser.add_argument('--server-url', default='http://localhost:8000', help='Server URL')
    parser.add_argument('--token', default='test-token', help='Agent token')
    parser.add_argument('--server-id', default='test-server-12345', help='Test server ID')
    
    args = parser.parse_args()
    
    tester = AgentTester(args.server_url, args.token)
    tester.server_id = args.server_id
    
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
