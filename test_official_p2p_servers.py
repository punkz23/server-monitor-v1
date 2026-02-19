#!/usr/bin/env python
"""
Test Official Dahua P2P Servers from PSS settings.ini
"""

import requests
import time

def test_p2p_servers():
    """Test connectivity to official Dahua P2P servers"""
    
    print("=" * 60)
    print("TESTING OFFICIAL DAHUA P2P SERVERS")
    print("=" * 60)
    
    # Official servers from PSS settings.ini
    servers = [
        "www.easy4ipcloud.com",
        "www.easy4ip.com", 
        "www.dahuap2pcloud.com",
        "www.dahuap2p.com",
        "p2p.dahua2.com",
        "p2p.easy4ipc.com",
        "p2p.dahuatech.com"
    ]
    
    # Test endpoints
    endpoints = [
        "/probe/p2psrv",
        "/api/probe", 
        "/p2p/probe",
        "/status",
        "/",
        "/api/v1/status"
    ]
    
    print(f"Testing {len(servers)} servers with {len(endpoints)} endpoints each...")
    print()
    
    working_servers = []
    
    for server in servers:
        print(f"Testing server: {server}")
        server_working = False
        
        for endpoint in endpoints:
            url = f"http://{server}{endpoint}"
            try:
                response = requests.get(url, timeout=10)
                status = response.status_code
                print(f"  {url} - Status: {status}")
                
                if status == 200:
                    working_servers.append((server, endpoint))
                    server_working = True
                    break
                elif status in [404, 405]:  # Common web server responses
                    print(f"    Server is reachable but endpoint not found")
                    
            except requests.exceptions.Timeout:
                print(f"  {url} - Timeout")
            except requests.exceptions.ConnectionError:
                print(f"  {url} - Connection refused")
            except Exception as e:
                print(f"  {url} - Error: {e}")
        
        if not server_working:
            print(f"  No working endpoints found for {server}")
        
        print()
        time.sleep(1)  # Rate limiting
    
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if working_servers:
        print("Working servers found:")
        for server, endpoint in working_servers:
            print(f"  {server}{endpoint}")
    else:
        print("No working servers found")
        print("\nPossible reasons:")
        print("1. Network connectivity issues")
        print("2. Servers require HTTPS")
        print("3. Servers require authentication")
        print("4. Different endpoint paths needed")
    
    print("\nRecommendations:")
    print("1. Try HTTPS instead of HTTP")
    print("2. Check if servers require specific headers")
    print("3. Look for device-specific endpoints")
    print("4. Test with actual device serial numbers")

if __name__ == "__main__":
    test_p2p_servers()
