#!/usr/bin/env python
"""
Test P2P connection implementation
"""

import os
import sys
import django

# Set up Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.dahua_p2p import test_p2p_connection, DahuaP2PClient

def test_p2p_devices():
    """Test P2P connection with your devices"""
    
    print("=" * 60)
    print("DAHUA P2P CONNECTION TEST")
    print("=" * 60)
    
    # Your device serial numbers
    devices = [
        '8K0C87BPAZC0B81',  # HEAD OFFICE
        '9G08CF2PAZ7F140',  # LIGAO
        '7D01D5APAZE99F3',  # MANILA
    ]
    
    for serial in devices:
        print(f"\n{'='*40}")
        print(f"Testing P2P Device: {serial}")
        print(f"{'='*40}")
        
        try:
            # Test basic P2P connection
            print("1. Testing P2P connection...")
            result = test_p2p_connection(serial)
            print(f"   Result: {'SUCCESS' if result else 'FAILED'}")
            
            # Test individual steps
            print("\n2. Testing P2P client initialization...")
            client = DahuaP2PClient(serial)
            print(f"   Client initialized for {client.serial_number}")
            
            print("\n3. Testing P2P server probe...")
            p2p_server = client.probe_p2p_server()
            print(f"   P2P Server: {p2p_server}")
            
            if p2p_server:
                print("\n4. Testing device status...")
                device_status = client.get_device_status(p2p_server)
                print(f"   Device Status: {device_status}")
                
                print("\n5. Testing device info...")
                device_info = client.get_device_info(p2p_server)
                print(f"   Device Info: {device_info}")
            
            print("\n6. Testing relay server...")
            relay_server = client.get_relay_info()
            print(f"   Relay Server: {relay_server}")
            
        except Exception as e:
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\n{'='*40}")
    
    print(f"\n{'='*60}")
    print("P2P TEST COMPLETE")
    print(f"{'='*60}")

if __name__ == "__main__":
    test_p2p_devices()
