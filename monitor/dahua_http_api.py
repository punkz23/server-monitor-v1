"""
Dahua HTTP API Client
Implements Dahua camera HTTP API for status checking and control
"""

import requests
import hashlib
import base64
import json
from urllib.parse import quote
import time


class DahuaHTTPClient:
    """Dahua HTTP API client for IP cameras and NVRs based on official SDK patterns"""
    
    def __init__(self, host, port=37777, username="admin", password="", timeout=10):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.timeout = timeout
        self.session_id = None
        self.base_url = f"http://{host}:{port}"
        
    def login(self):
        """Login to Dahua device using SDK pattern"""
        try:
            # Method 1: New RPC2 API format (from SDK docs)
            login_url = f"{self.base_url}/RPC2_Login"
            data = {
                "method": "global.login",
                "params": {
                    "userName": self.username,
                    "password": "",
                    "clientType": "Web3.0"
                },
                "id": 1,
                "session": None
            }
            
            response = requests.post(login_url, json=data, timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("result"):
                    session = result["result"]
                    self.session_id = session.get("sessionId")
                    
                    # Handle password encryption (SDK pattern)
                    if "password" in session and session["password"]:
                        encrypted_password = self._encrypt_password(session["password"])
                        data["params"]["password"] = encrypted_password
                        data["session"] = self.session_id
                        
                        # Retry login with encrypted password
                        response = requests.post(login_url, json=data, timeout=self.timeout)
                        if response.status_code == 200:
                            result = response.json()
                            if result.get("result"):
                                self.session_id = result["result"].get("sessionId")
                                return True
                    
                    return True
            
            # Method 2: Legacy login
            return self._legacy_login()
            
        except Exception as e:
            print(f"Login error: {e}")
            return False
    
    def get_all_channels(self):
        """Get all IP channels for NVR (SDK pattern)"""
        if not self.session_id and not self.login():
            return []
            
        try:
            channels_url = f"{self.base_url}/RPC2"
            data = {
                "method": "videoInput.getAllChannels",
                "params": {},
                "id": 2,
                "session": self.session_id
            }
            
            response = requests.post(channels_url, json=data, timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("result"):
                    channels = result["result"]
                    return [{"id": ch.get("id", 0), "name": ch.get("name", f"Channel{ch.get('id', 0)}")} for ch in channels]
                    
        except Exception as e:
            print(f"Get channels error: {e}")
            
        return []
    
    def get_machine_name(self):
        """Get machine name (SDK pattern)"""
        if not self.session_id and not self.login():
            return None
            
        try:
            name_url = f"{self.base_url}/RPC2"
            data = {
                "method": "configManager.getConfig",
                "params": {
                    "name": "MachineName"
                },
                "id": 3,
                "session": self.session_id
            }
            
            response = requests.post(name_url, json=data, timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("result"):
                    return result["result"].get("table", {}).get("MachineName", {}).get("value")
                    
        except Exception as e:
            print(f"Get machine name error: {e}")
            
        return None
    
    def get_device_serial_number(self):
        """Get device serial number (SDK pattern)"""
        if not self.session_id and not self.login():
            return None
            
        try:
            serial_url = f"{self.base_url}/RPC2"
            data = {
                "method": "configManager.getConfig",
                "params": {
                    "name": "General"
                },
                "id": 4,
                "session": self.session_id
            }
            
            response = requests.post(serial_url, json=data, timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("result"):
                    return result["result"].get("table", {}).get("General", {}).get("SerialNo")
                    
        except Exception as e:
            print(f"Get serial number error: {e}")
            
        return None
    
    def get_device_type(self):
        """Get device type (SDK pattern)"""
        if not self.session_id and not self.login():
            return None
            
        try:
            type_url = f"{self.base_url}/RPC2"
            data = {
                "method": "magicBox.getDeviceType",
                "params": {},
                "id": 5,
                "session": self.session_id
            }
            
            response = requests.post(type_url, json=data, timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("result"):
                    return result["result"].get("type")
                    
        except Exception as e:
            print(f"Get device type error: {e}")
            
        return None
    
    def get_current_time(self):
        """Get device current time (SDK pattern)"""
        if not self.session_id and not self.login():
            return None
            
        try:
            time_url = f"{self.base_url}/RPC2"
            data = {
                "method": "global.getCurrentTime",
                "params": {},
                "id": 6,
                "session": self.session_id
            }
            
            response = requests.post(time_url, json=data, timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("result"):
                    return result["result"].get("time")
                    
        except Exception as e:
            print(f"Get current time error: {e}")
            
        return None
    
    def find_videos(self, start_time, end_time, channel=0):
        """Find videos list (SDK pattern)"""
        if not self.session_id and not self.login():
            return []
            
        try:
            videos_url = f"{self.base_url}/RPC2"
            data = {
                "method": "mediaFile.find",
                "params": {
                    "StartTime": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "EndTime": end_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "Channel": channel,
                    "Type": "all"
                },
                "id": 7,
                "session": self.session_id
            }
            
            response = requests.post(videos_url, json=data, timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("result"):
                    files = result["result"].get("file", [])
                    return [{
                        "name": f.get("Name", ""),
                        "size": f.get("Size", 0),
                        "start_time": f.get("StartTime", ""),
                        "end_time": f.get("EndTime", "")
                    } for f in files]
                    
        except Exception as e:
            print(f"Find videos error: {e}")
            
        return []
    
    def _legacy_login(self):
        """Legacy login method for older Dahua firmware"""
        try:
            login_url = f"{self.base_url}/cgi-bin/global.cgi"
            params = {
                "action": "login",
                "username": self.username,
                "password": self.password
            }
            
            response = requests.get(login_url, params=params, timeout=self.timeout)
            
            if response.status_code == 200 and "OK" in response.text:
                # Extract session ID from response
                if "session_id=" in response.text:
                    self.session_id = response.text.split("session_id=")[1].split("&")[0]
                return True
                
        except Exception as e:
            print(f"Legacy login error: {e}")
            
        return False
    
    def _encrypt_password(self, random):
        """Encrypt password using Dahua's method"""
        if not random:
            return self.password
            
        # Reverse the random string
        reversed_random = random[::-1]
        
        # Create MD5 hash of password + reversed random
        combined = (self.password + reversed_random).encode('utf-8')
        md5_hash = hashlib.md5(combined).hexdigest()
        
        return md5_hash
    
    def get_device_info(self):
        """Get device information"""
        if not self.session_id and not self.login():
            return None
            
        try:
            info_url = f"{self.base_url}/RPC2"
            data = {
                "method": "global.getDeviceType",
                "params": {},
                "id": 2,
                "session": self.session_id
            }
            
            response = requests.post(info_url, json=data, timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("result"):
                    return result["result"]
                    
        except Exception as e:
            print(f"Get device info error: {e}")
            
        return None
    
    def get_camera_status(self):
        """Get camera status and capabilities"""
        if not self.session_id and not self.login():
            return None
            
        try:
            # Get camera information
            status_url = f"{self.base_url}/RPC2"
            data = {
                "method": "videoInput.getCurrentInfo",
                "params": {},
                "id": 3,
                "session": self.session_id
            }
            
            response = requests.post(status_url, json=data, timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("result"):
                    return result["result"]
                    
        except Exception as e:
            print(f"Get camera status error: {e}")
            
        return None
    
    def get_stream_info(self, channel=0):
        """Get streaming information for a channel"""
        if not self.session_id and not self.login():
            return None
            
        try:
            stream_url = f"{self.base_url}/RPC2"
            data = {
                "method": "media.getStreamInfo",
                "params": {
                    "channel": channel
                },
                "id": 4,
                "session": self.session_id
            }
            
            response = requests.post(stream_url, json=data, timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("result"):
                    return result["result"]
                    
        except Exception as e:
            print(f"Get stream info error: {e}")
            
        return None
    
    def get_system_info(self):
        """Get system information"""
        if not self.session_id and not self.login():
            return None
            
        try:
            system_url = f"{self.base_url}/RPC2"
            data = {
                "method": "system.getSystemInfo",
                "params": {},
                "id": 5,
                "session": self.session_id
            }
            
            response = requests.post(system_url, json=data, timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("result"):
                    return result["result"]
                    
        except Exception as e:
            print(f"Get system info error: {e}")
            
        return None
    
    def logout(self):
        """Logout from the device"""
        if self.session_id:
            try:
                logout_url = f"{self.base_url}/RPC2"
                data = {
                    "method": "global.logout",
                    "params": {},
                    "id": 6,
                    "session": self.session_id
                }
                
                requests.post(logout_url, json=data, timeout=self.timeout)
            except:
                pass
            finally:
                self.session_id = None
    
    def test_connection(self):
        """Test basic connection to the device"""
        try:
            # Try to reach the device's web interface
            response = requests.get(f"{self.base_url}/", timeout=self.timeout)
            
            if response.status_code in [200, 401, 403]:
                # Device is reachable
                if "Dahua" in response.text or "dahua" in response.text.lower():
                    return True, "Dahua device detected"
                else:
                    return True, "Device reachable but may not be Dahua"
            else:
                return False, f"HTTP {response.status_code}"
                
        except Exception as e:
            return False, str(e)


def check_dahua_camera_status(host, port=80, username="admin", password="admin123456"):
    """Check Dahua camera status using HTTP API"""
    
    print(f"=== Checking Dahua Camera: {host}:{port} ===")
    
    client = DahuaHTTPClient(host, port, username, password)
    
    # Test basic connection first
    reachable, message = client.test_connection()
    print(f"Basic connection test: {reachable} - {message}")
    
    if not reachable:
        return False
    
    # Try to get device info
    try:
        device_info = client.get_device_info()
        if device_info:
            print(f"Device info retrieved: {device_info}")
            client.logout()
            return True
    except:
        pass
    
    # Try alternative method - check for camera streams
    try:
        stream_info = client.get_stream_info()
        if stream_info:
            print(f"Stream info retrieved: {stream_info}")
            client.logout()
            return True
    except:
        pass
    
    # If API calls fail but device is reachable, assume it's online
    print("Device reachable but API calls failed - assuming online")
    client.logout()
    return True


def get_dahua_rtsp_url(host, port=554, username="admin", password="admin123456", channel=0):
    """Generate RTSP URL for Dahua camera"""
    
    # Common RTSP URL formats for Dahua
    formats = [
        f"rtsp://{username}:{password}@{host}:{port}/cam/realmonitor?channel={channel}&subtype=0",
        f"rtsp://{username}:{password}@{host}:{port}/cam/realmonitor?channel={channel}&subtype=1",
        f"rtsp://{username}:{password}@{host}:{port}/stream1",
        f"rtsp://{username}:{password}@{host}:{port}/live/{channel}",
        f"rtsp://{username}:{password}@{host}:{port}/h264/ch{channel}/main/av_stream"
    ]
    
    return formats[0]  # Return the most common format
