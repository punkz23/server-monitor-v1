"""
Simple network connectivity test
"""
import socket
import requests

def test_basic_connectivity():
    """Test basic internet connectivity"""
    print("=== Testing Basic Internet Connectivity ===")
    
    # Test DNS resolution
    try:
        ip = socket.gethostbyname("google.com")
        print(f"DNS resolution works: google.com -> {ip}")
    except Exception as e:
        print(f"DNS resolution failed: {e}")
        return False
    
    # Test HTTP request
    try:
        response = requests.get("http://httpbin.org/ip", timeout=5)
        print(f"HTTP requests work: {response.status_code}")
    except Exception as e:
        print(f"HTTP requests failed: {e}")
        return False
    
    # Test HTTPS request
    try:
        response = requests.get("https://httpbin.org/ip", timeout=5)
        print(f"HTTPS requests work: {response.status_code}")
    except Exception as e:
        print(f"HTTPS requests failed: {e}")
        return False
    
    return True

def test_dahua_servers():
    """Test connectivity to Dahua servers"""
    print("\n=== Testing Dahua Server Connectivity ===")
    
    servers = [
        "dahuatech.com",
        "dahuavision.com", 
        "p2p.dahuatech.com",
        "p2p.dahuavision.com"
    ]
    
    for server in servers:
        try:
            response = requests.get(f"http://{server}", timeout=5)
            print(f"{server}: HTTP {response.status_code}")
        except Exception as e:
            print(f"{server}: Failed - {e}")
        
        try:
            response = requests.get(f"https://{server}", timeout=5, verify=False)
            print(f"{server}: HTTPS {response.status_code}")
        except Exception as e:
            print(f"{server}: HTTPS Failed - {e}")

if __name__ == "__main__":
    test_basic_connectivity()
    test_dahua_servers()
