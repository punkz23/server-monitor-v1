#!/usr/bin/env python
"""Script to test network access and provide VPN setup guidance"""

import os
import sys
import subprocess
import socket
from ipaddress import ip_address, ip_network

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
import django
django.setup()

import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_current_connectivity():
    """Test current network connectivity to 172.10.10.0/24"""
    print("Testing Current Network Connectivity")
    print("=" * 50)
    
    # Test if we can reach firewall
    try:
        firewall_socket = socket.create_connection(("192.168.253.2", 4444), timeout=5)
        firewall_socket.close()
        print("✓ Can reach firewall at 192.168.253.2:4444")
    except Exception as e:
        print(f"✗ Cannot reach firewall: {e}")
        return False
    
    # Test direct ping to 172.10.10.1 (firewall interface)
    try:
        result = subprocess.run(['ping', '-n', '2', '172.10.10.1'], 
                          capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✓ Can ping 172.10.10.1 (firewall interface)")
        else:
            print("✗ Cannot ping 172.10.10.1")
    except Exception as e:
        print(f"✗ Ping test failed: {e}")
    
    # Test if route exists
    try:
        result = subprocess.run(['route', 'print'], capture_output=True, text=True)
        if '172.10.10.0' in result.stdout:
            print("✓ Route to 172.10.10.0/24 exists")
        else:
            print("✗ No route to 172.10.10.0/24")
    except Exception as e:
        print(f"✗ Route check failed: {e}")
    
    return True

def setup_temporary_route():
    """Setup temporary route through firewall"""
    print("\nSetting Up Temporary Route")
    print("=" * 50)
    
    commands = [
        # Add route through firewall
        f'route add 172.10.10.0 mask 255.255.255.0 192.168.253.2',
        # Test connectivity after route
        'ping -n 2 172.10.10.1',
        'ping -n 2 172.10.10.10'
    ]
    
    for cmd in commands:
        print(f"Running: {cmd}")
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
            print(f"Exit code: {result.returncode}")
            if result.stdout:
                print(f"Output: {result.stdout[:200]}")
            if result.stderr:
                print(f"Error: {result.stderr[:200]}")
        except Exception as e:
            print(f"Failed: {e}")
        print("-" * 30)
    
    print("\nTo remove this route later, run:")
    print("route delete 172.10.10.0")

def provide_vpn_setup_instructions():
    """Provide detailed VPN setup instructions"""
    print("\nVPN Setup Instructions")
    print("=" * 50)
    
    print("1. SOPHOS FIREWALL SSL VPN SETUP:")
    print("   a) Access: https://192.168.253.2:4444")
    print("   b) Login: francois_ignacio")
    print("   c) Navigate: VPN > SSL VPN")
    print("   d) Click 'Add' to create new SSL VPN")
    print("   e) Configure:")
    print("      - Name: Admin-172.10.10-Access")
    print("      - Authentication: Use existing user or create VPN user")
    print("      - Network: 172.10.10.0")
    print("      - Netmask: 255.255.255.0")
    print("      - Gateway: 172.10.10.1")
    print("   f) Save and enable")
    
    print("\n2. CONNECT TO VPN:")
    print("   a) Download Sophos Connect client from firewall")
    print("   b) Install client")
    print("   c) Import configuration or enter:")
    print("      - Gateway: 192.168.253.2")
    print("      - Username: your VPN username")
    print("      - Password: your VPN password")
    print("   d) Connect")
    
    print("\n3. ALTERNATIVE - L2TP VPN:")
    print("   a) In Sophos: VPN > L2TP Server")
    print("   b) Enable L2TP with pre-shared key")
    print("   c) On Windows: Settings > Network & Internet > VPN")
    print("   d) Add VPN: L2TP/IPSec")
    print("      - Server: 192.168.253.2")
    print("      - VPN type: L2TP/IPSec with pre-shared key")
    
    print("\n4. TEST AFTER VPN CONNECTION:")
    print("   a) Run: ping 172.10.10.1")
    print("   b) Run: ping 172.10.10.10")
    print("   c) Run: python scan_network.py")
    print("   d) Check if 172.10.10.0/24 appears in local networks")

def create_vpn_connection_script():
    """Create Windows PowerShell script for VPN setup"""
    script_content = """
# Sophos VPN Setup Script
# Run as Administrator

Write-Host "Sophos Firewall VPN Setup" -ForegroundColor Green
Write-Host "==========================" -ForegroundColor Green

# Add temporary route through firewall
Write-Host "Adding route through firewall..." -ForegroundColor Yellow
try {
    route add 172.10.10.0 mask 255.255.255.0 192.168.253.2
    Write-Host "✓ Route added successfully" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to add route" -ForegroundColor Red
}

# Test connectivity
Write-Host "Testing connectivity..." -ForegroundColor Yellow
try {
    Test-Connection -ComputerName 172.10.10.1 -Count 2 -ErrorAction Stop
    Write-Host "✓ Can reach 172.10.10.1" -ForegroundColor Green
} catch {
    Write-Host "✗ Cannot reach 172.10.10.1" -ForegroundColor Red
}

try {
    Test-Connection -ComputerName 172.10.10.10 -Count 2 -ErrorAction Stop
    Write-Host "✓ Can reach 172.10.10.10" -ForegroundColor Green
} catch {
    Write-Host "✗ Cannot reach 172.10.10.10" -ForegroundColor Red
}

Write-Host ""
Write-Host "To remove route later, run:" -ForegroundColor Yellow
Write-Host "route delete 172.10.10.0" -ForegroundColor Yellow

Write-Host ""
Write-Host "For permanent VPN access, configure SSL VPN in Sophos admin console" -ForegroundColor Cyan
"""
    
    with open('setup_vpn_access.ps1', 'w') as f:
        f.write(script_content)
    
    print("\n✓ Created PowerShell script: setup_vpn_access.ps1")
    print("Run as Administrator: powershell -ExecutionPolicy Bypass -File setup_vpn_access.ps1")

def main():
    """Main function"""
    print("VPN Access Setup for 172.10.10.0/24 Network")
    print("=" * 60)
    
    # Test current connectivity
    test_current_connectivity()
    
    # Setup temporary route
    setup_temporary_route()
    
    # Provide VPN instructions
    provide_vpn_setup_instructions()
    
    # Create setup script
    create_vpn_connection_script()
    
    print("\nNext Steps:")
    print("1. Try the temporary route method above")
    print("2. If route works, configure permanent VPN in Sophos console")
    print("3. Once connected, run: python scan_network.py")
    print("4. Check if 172.10.10.0/24 devices appear in scan results")

if __name__ == "__main__":
    main()
