"""
Dahua RPC SDK for Python
Based on https://github.com/naveenrobo/dahua-ip-cam-sdk
Provides direct camera communication for live feeds and events
"""

import requests
import json
import hashlib
import time
from urllib.parse import quote


class DahuaRpc:
    """Dahua RPC client for IP cameras"""
    
    def __init__(self, host, username="admin", password="", port=80, timeout=10):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.timeout = timeout
        self.session_id = None
        self.base_url = f"http://{host}:{port}"
        
    def login(self):
        """Login to camera and create session"""
        try:
            # First login attempt
            login_data = {
                "method": "global.login",
                "params": {
                    "userName": self.username,
                    "password": "",
                    "clientType": "Dahua_RPC"
                },
                "id": 1
            }
            
            response = requests.post(f"{self.base_url}/RPC2_Login", json=login_data, timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("result"):
                    session = result["result"]
                    self.session_id = session.get("sessionId")
                    
                    # Handle password encryption if required
                    if "password" in session and session["password"]:
                        encrypted_password = self._encrypt_password(session["password"])
                        login_data["params"]["password"] = encrypted_password
                        login_data["session"] = self.session_id
                        
                        # Retry with encrypted password
                        response = requests.post(f"{self.base_url}/RPC2_Login", json=login_data, timeout=self.timeout)
                        if response.status_code == 200:
                            result = response.json()
                            if result.get("result"):
                                self.session_id = result["result"].get("sessionId")
                                return True
                    
                    return True
            
            return False
            
        except Exception as e:
            print(f"Login error: {e}")
            return False
    
    def _encrypt_password(self, random):
        """Encrypt password using Dahua's method"""
        if not random:
            return self.password
            
        # Reverse the random string and create MD5 hash
        reversed_random = random[::-1]
        combined = (self.password + reversed_random).encode('utf-8')
        md5_hash = hashlib.md5(combined).hexdigest()
        
        return md5_hash
    
    def request(self, method, params=None, object_id=None):
        """Make raw RPC request"""
        if not self.session_id and not self.login():
            return None
            
        try:
            data = {
                "method": method,
                "params": params or {},
                "id": int(time.time()),
                "session": self.session_id
            }
            
            if object_id:
                data["object"] = object_id
            
            response = requests.post(f"{self.base_url}/RPC2", json=data, timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("result"):
                    return result["result"]
                elif result.get("error"):
                    print(f"RPC Error: {result['error']}")
                    return None
                    
        except Exception as e:
            print(f"RPC request error: {e}")
            
        return None
    
    def current_time(self):
        """Get current time on device"""
        return self.request("global.getCurrentTime")
    
    def set_split(self, mode=4, view=1):
        """Set display to grids with view group"""
        return self.request("videoInput.setSplit", {"mode": mode, "view": view})
    
    def get_serial_number(self):
        """Get device serial number"""
        return self.request("magicBox.getSerialNo")
    
    def get_device_info(self):
        """Get device information"""
        return self.request("magicBox.getDeviceType")
    
    def get_camera_info(self):
        """Get camera information"""
        return self.request("videoInput.getCurrentInfo")
    
    def get_stream_info(self, channel=0):
        """Get streaming information"""
        return self.request("media.getStreamInfo", {"channel": channel})
    
    def get_live_stream_url(self, channel=0, subtype=0):
        """Generate live stream URL"""
        # Common Dahua RTSP URL patterns
        patterns = [
            f"rtsp://{self.username}:{self.password}@{self.host}:554/cam/realmonitor?channel={channel+1}&subtype={subtype}",
            f"rtsp://{self.username}:{self.password}@{self.host}:554/stream1",
            f"rtsp://{self.username}:{self.password}@{self.host}:554/live/{channel}",
            f"rtsp://{self.username}:{self.password}@{self.host}:554/h264/ch{channel+1}/main/av_stream"
        ]
        
        return patterns[0]  # Return most common pattern
    
    def get_snapshot(self, channel=0):
        """Get current snapshot from camera"""
        try:
            snapshot_url = f"{self.base_url}/cgi-bin/snapshot.cgi"
            params = {
                "channel": channel,
                "username": self.username,
                "password": self.password
            }
            
            response = requests.get(snapshot_url, params=params, timeout=self.timeout)
            
            if response.status_code == 200 and response.headers.get('content-type', '').startswith('image'):
                return response.content
                
        except Exception as e:
            print(f"Snapshot error: {e}")
            
        return None
    
    def get_traffic_info(self):
        """Get traffic/ANPR object ID"""
        return self.request("trafficCar.getTrafficData")
    
    def start_find(self, object_id):
        """Start finding operation"""
        return self.request("recordFinder.startFind", {"object": object_id})
    
    def do_find(self, object_id):
        """Execute find operation"""
        return self.request("recordFinder.doFind", {"object": object_id})
    
    def attach_event(self, events):
        """Attach to camera events"""
        return self.request("eventManager.attach", {"codes": events})
    
    def listen_events(self, callback):
        """Listen for camera events"""
        try:
            events_url = f"{self.base_url}/RPC2_Event"
            
            while True:
                try:
                    response = requests.get(events_url, timeout=30)
                    if response.status_code == 200:
                        data = response.json()
                        if data:
                            callback(data)
                except Exception as e:
                    print(f"Event listening error: {e}")
                    time.sleep(5)
                    
        except KeyboardInterrupt:
            print("Event listening stopped")
    
    def get_live_frame(self, channel=0):
        """Get live frame data for streaming"""
        try:
            # Try MJPEG stream first
            mjpeg_url = f"{self.base_url}/cgi-bin/mjpg/video.cgi?channel={channel}"
            response = requests.get(mjpeg_url, timeout=5, stream=True)
            
            if response.status_code == 200:
                return response.raw
                
        except Exception as e:
            print(f"Live frame error: {e}")
            
        return None
    
    def logout(self):
        """Logout from camera"""
        if self.session_id:
            try:
                self.request("global.logout")
                self.session_id = None
                return True
            except:
                pass
        return False


def get_dahua_live_feed(host, username="admin", password="admin123456", channel=0):
    """Get live feed from Dahua camera"""
    
    print(f"=== Getting Dahua Live Feed: {host} ===")
    
    try:
        # Initialize RPC client
        dahua = DahuaRpc(host, username, password)
        
        # Login to camera
        if not dahua.login():
            print("Failed to login to camera")
            return None
        
        print(f"Successfully logged in to {host}")
        
        # Get camera info
        camera_info = dahua.get_camera_info()
        if camera_info:
            print(f"Camera info: {camera_info}")
        
        # Get stream URL
        stream_url = dahua.get_live_stream_url(channel)
        print(f"Stream URL: {stream_url}")
        
        # Get snapshot
        snapshot = dahua.get_snapshot(channel)
        if snapshot:
            print(f"Got snapshot: {len(snapshot)} bytes")
        
        # Get live frame for streaming
        live_frame = dahua.get_live_frame(channel)
        if live_frame:
            print("Live frame stream available")
        
        # Logout
        dahua.logout()
        
        return {
            'stream_url': stream_url,
            'snapshot': snapshot,
            'live_frame': live_frame,
            'camera_info': camera_info,
            'status': 'online'
        }
        
    except Exception as e:
        print(f"Live feed error: {e}")
        return None


def test_dahua_connection(host, username="admin", password="admin123456"):
    """Test connection to Dahua camera"""
    
    print(f"=== Testing Dahua Connection: {host} ===")
    
    try:
        dahua = DahuaRpc(host, username, password)
        
        if dahua.login():
            # Test basic functions
            current_time = dahua.current_time()
            serial_number = dahua.get_serial_number()
            device_info = dahua.get_device_info()
            
            print(f"Connection successful!")
            print(f"Current time: {current_time}")
            print(f"Serial number: {serial_number}")
            print(f"Device info: {device_info}")
            
            dahua.logout()
            return True
        else:
            print("Login failed")
            return False
            
    except Exception as e:
        print(f"Connection test error: {e}")
        return False
