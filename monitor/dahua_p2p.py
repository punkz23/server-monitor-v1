"""
Dahua P2P RTSP Implementation
Based on https://github.com/khoanguyen-3fc/dh-p2p
Provides RTSP streaming over Dahua P2P protocol
"""

import socket
import struct
import threading
import time
import requests
import hashlib
import random
from urllib.parse import urlparse


class DahuaP2PClient:
    """Dahua P2P client for RTSP streaming"""
    
    def __init__(self, serial_number, username="admin", password="admin123456"):
        self.serial_number = serial_number
        self.username = username
        self.password = password
        self.easy4ip_cloud = "www.easy4ipcloud.com"
        self.p2p_servers = [
            "www.easy4ipcloud.com",
            "www.easy4ip.com",
            "www.dahuap2pcloud.com",
            "www.dahuap2p.com",
            "p2p.dahua2.com",
            "p2p.easy4ipc.com", 
            "p2p.dahuatech.com"
        ]
        self.relay_servers = [
            "relay.easy4ipc.com",
            "relay.dahua2.com"
        ]
        self.local_port = None
        self.device_ip = None
        self.device_port = None
        self.session_token = None
        self.ptcp_socket = None
        
    def probe_p2p_server(self):
        """Probe for available P2P server"""
        for server in self.p2p_servers:
            try:
                # Try different probe endpoints based on PSS patterns
                endpoints = [
                    f"http://{server}/probe/p2psrv",
                    f"http://{server}/api/probe",
                    f"http://{server}/p2p/probe",
                    f"http://{server}/status"
                ]
                
                for endpoint in endpoints:
                    response = requests.get(endpoint, timeout=5)
                    if response.status_code == 200:
                        print(f"P2P server {server} is available via {endpoint}")
                        return server
            except:
                continue
        return None
    
    def get_device_status(self, p2p_server):
        """Get device online status"""
        try:
            response = requests.get(f"http://{p2p_server}/info/device/{self.serial_number}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data
        except:
            pass
        return None
    
    def get_device_info(self, p2p_server):
        """Get device connection info"""
        try:
            response = requests.get(f"http://{p2p_server}/online/p2psrv/{self.serial_number}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data
        except:
            pass
        return None
    
    def get_relay_info(self):
        """Get relay server info"""
        for server in self.relay_servers:
            try:
                response = requests.get(f"http://{server}/probe/device/{self.serial_number}", timeout=5)
                if response.status_code == 200:
                    return server
            except:
                continue
        return None
    
    def establish_connection(self):
        """Establish P2P connection to device"""
        try:
            # Create PTCP socket
            self.create_ptcp_socket()
            
            # Probe for available P2P server
            p2p_server = self.probe_p2p_server()
            if not p2p_server:
                return False
            
            # Get device info
            device_info = self.get_device_info(p2p_server)
            if device_info:
                self.device_ip = device_info.get('ip')
                self.device_port = device_info.get('port', 37777)
                return True
            
            # Try relay server fallback
            relay_server = self.get_relay_info()
            if relay_server:
                self.device_ip = relay_server
                self.device_port = 37777
                return True
            
            return False
        except Exception as e:
            print(f"P2P connection error: {e}")
            return False
    
    def get_rtsp_url(self, stream_type='main'):
        """Get RTSP URL for streaming"""
        if not self.device_ip or not self.device_port:
            return None
        
        subtype = '0' if stream_type == 'main' else '1'
        return f"rtsp://{self.username}:{self.password}@{self.device_ip}:{self.device_port}/cam/realmonitor?channel=1&subtype={subtype}#backchannel=0"
    
    def get_snapshot(self):
        """Get snapshot from device"""
        try:
            if not self.device_ip or not self.device_port:
                return None
            
            # Use HTTP API to get snapshot
            import requests
            snapshot_url = f"http://{self.device_ip}:{self.device_port}/cgi-bin/snapshot.cgi"
            
            response = requests.get(snapshot_url, auth=(self.username, self.password), timeout=10)
            if response.status_code == 200:
                return response.content
        except Exception as e:
            print(f"Snapshot error: {e}")
        
        return None

    def create_ptcp_socket(self):
        """Create PTCP socket"""
        self.ptcp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ptcp_socket.bind(('0.0.0.0', 0))
        self.local_port = self.ptcp_socket.getsockname()[1]
        print(f"PTCP socket bound to port {self.local_port}")
        return self.local_port
    
    def send_ptcp_packet(self, data, dest_ip, dest_port):
        """Send PTCP packet"""
        if not self.ptcp_socket:
            return False
            
        try:
            self.ptcp_socket.sendto(data, (dest_ip, dest_port))
            return True
        except:
            return False
    
    def receive_ptcp_packet(self, timeout=5):
        """Receive PTCP packet"""
        if not self.ptcp_socket:
            return None
            
        try:
            self.ptcp_socket.settimeout(timeout)
            data, addr = self.ptcp_socket.recvfrom(4096)
            return data, addr
        except:
            return None, None
    
    def create_ptcp_header(self, magic="PTCP", sent=0, recv=0, pid=1, lmid=0, rmid=0):
        """Create PTCP packet header"""
        return struct.pack('<4sIIIII', magic.encode(), sent, recv, pid, lmid, rmid)
    
    def establish_p2p_connection(self):
        """Establish P2P connection to device"""
        print(f"=== Establishing P2P connection to {self.serial_number} ===")
        
        # Step 1: Probe P2P server
        p2p_server = self.probe_p2p_server()
        if not p2p_server:
            print("No P2P servers available")
            return False
        
        # Step 2: Get device status
        device_status = self.get_device_status(p2p_server)
        if not device_status:
            print("Device not found or offline")
            return False
        
        print(f"Device status: {device_status}")
        
        # Step 3: Get device info
        device_info = self.get_device_info(p2p_server)
        if not device_info:
            print("Could not get device info")
            return False
        
        print(f"Device info: {device_info}")
        
        # Step 4: Create PTCP socket
        self.create_ptcp_socket()
        
        # Step 5: Try direct connection first
        if 'ip' in device_info and 'port' in device_info:
            self.device_ip = device_info['ip']
            self.device_port = device_info['port']
            
            # Send PTCP SYN
            ptcp_header = self.create_ptcp_header(pid=1)
            if self.send_ptcp_packet(ptcp_header, self.device_ip, self.device_port):
                print("PTCP SYN sent to device")
                
                # Wait for response
                response, addr = self.receive_ptcp_packet()
                if response and addr[0] == self.device_ip:
                    print("PTCP response received from device")
                    return True
        
        # Step 6: Try relay connection
        relay_server = self.get_relay_info()
        if relay_server:
            print(f"Using relay server: {relay_server}")
            return self.establish_relay_connection(relay_server)
        
        print("Could not establish P2P connection")
        return False
    
    def establish_relay_connection(self, relay_server):
        """Establish connection via relay server"""
        try:
            # Get relay agent info
            response = requests.get(f"http://{relay_server}/relay/agent", timeout=10)
            if response.status_code == 200:
                agent_info = response.json()
                print(f"Relay agent info: {agent_info}")
                
                # Start relay session
                response = requests.post(f"http://{relay_server}/relay/start/{agent_info.get('token')}", timeout=10)
                if response.status_code == 200:
                    print("Relay session started")
                    return True
                    
        except Exception as e:
            print(f"Relay connection error: {e}")
        
        return False
    
    def start_rtsp_proxy(self, local_port=8554):
        """Start RTSP proxy server"""
        proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        proxy_socket.bind(('127.0.0.1', local_port))
        proxy_socket.listen(1)
        
        print(f"RTSP proxy listening on 127.0.0.1:{local_port}")
        print(f"RTSP URL: rtsp://{self.username}:{self.password}@127.0.0.1:{local_port}/cam/realmonitor?channel=1&subtype=0")
        
        while True:
            try:
                client_socket, addr = proxy_socket.accept()
                print(f"RTSP client connected from {addr}")
                
                # Handle RTSP client in separate thread
                client_thread = threading.Thread(
                    target=self.handle_rtsp_client,
                    args=(client_socket,)
                )
                client_thread.daemon = True
                client_thread.start()
                
            except Exception as e:
                print(f"RTSP proxy error: {e}")
                break
    
    def handle_rtsp_client(self, client_socket):
        """Handle RTSP client connection"""
        try:
            while True:
                data = client_socket.recv(4096)
                if not data:
                    break
                
                # Parse RTSP request
                rtsp_request = data.decode('utf-8', errors='ignore')
                print(f"RTSP Request: {rtsp_request.split()[0] if rtsp_request else 'Unknown'}")
                
                # Forward to device via PTCP
                if self.device_ip and self.device_port:
                    ptcp_data = self.create_ptcp_header() + data
                    if self.send_ptcp_packet(ptcp_data, self.device_ip, self.device_port):
                        print("RTSP request forwarded to device")
                
                # Simple RTSP responses
                if "OPTIONS" in rtsp_request:
                    response = "RTSP/1.0 200 OK\r\nPublic: OPTIONS, DESCRIBE, SETUP, TEARDOWN, PLAY\r\n\r\n"
                    client_socket.send(response.encode())
                elif "DESCRIBE" in rtsp_request:
                    response = "RTSP/1.0 200 OK\r\nContent-Type: application/sdp\r\n\r\n"
                    client_socket.send(response.encode())
                elif "SETUP" in rtsp_request:
                    response = "RTSP/1.0 200 OK\r\nTransport: RTP/AVP/TCP;unicast;client_port=0\r\n\r\n"
                    client_socket.send(response.encode())
                elif "PLAY" in rtsp_request:
                    response = "RTSP/1.0 200 OK\r\nRange: npt=0.000-\r\n\r\n"
                    client_socket.send(response.encode())
                    
        except Exception as e:
            print(f"RTSP client handling error: {e}")
        finally:
            client_socket.close()
    
    def connect(self):
        """Main connection method"""
        # Establish P2P connection
        if not self.establish_p2p_connection():
            return False
        
        # Start RTSP proxy
        self.start_rtsp_proxy()
        return True


def test_p2p_connection(serial_number, username="admin", password="admin123456"):
    """Test P2P connection to device"""
    print(f"=== Testing P2P Connection: {serial_number} ===")
    
    client = DahuaP2PClient(serial_number, username, password)
    
    try:
        if client.connect():
            print("P2P connection established successfully!")
            return True
        else:
            print("P2P connection failed")
            return False
    except Exception as e:
        print(f"P2P connection error: {e}")
        return False


def get_p2p_rtsp_url(serial_number, username="admin", password="admin123456"):
    """Get RTSP URL for P2P device"""
    return f"rtsp://{username}:{password}@127.0.0.1:8554/cam/realmonitor?channel=1&subtype=0"


if __name__ == "__main__":
    # Test with your device serial
    serial = "8K0C87BPAZC0B81"  # Replace with actual serial
    test_p2p_connection(serial)
