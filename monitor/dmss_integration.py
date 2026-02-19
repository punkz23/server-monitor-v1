"""
DMSS (Dahua Mobile Security Service) Cloud Integration
Provides cloud access to Dahua devices via DMSS account
"""

import requests
import json
import hashlib
import time
import base64
from urllib.parse import urljoin
from django.core.cache import cache


class DMSSClient:
    """DMSS cloud client for Dahua device management"""
    
    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password
        self.base_url = "https://dmss.dahua.com"
        self.api_url = "https://dmss.dahua.com/api"
        self.session = requests.Session()
        self.token = None
        self.user_id = None
        self.devices = []
        
    def login(self, username=None, password=None):
        """Login to DMSS cloud service"""
        if username and password:
            self.username = username
            self.password = password
            
        if not self.username or not self.password:
            return False, "Username and password required"
        
        try:
            # DMSS login endpoint
            login_url = f"{self.api_url}/login"
            
            login_data = {
                "username": self.username,
                "password": self.password,
                "clientType": "web",
                "language": "en_US"
            }
            
            response = self.session.post(login_url, json=login_data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("code") == 0:
                    data = result.get("data", {})
                    self.token = data.get("token")
                    self.user_id = data.get("userId")
                    
                    # Store session
                    cache.set('dmss_token', self.token, 3600)
                    cache.set('dmss_user_id', self.user_id, 3600)
                    
                    return True, "Login successful"
                else:
                    return False, result.get("msg", "Login failed")
            else:
                return False, f"HTTP {response.status_code}"
                
        except Exception as e:
            return False, str(e)
    
    def logout(self):
        """Logout from DMSS cloud service"""
        try:
            if self.token:
                logout_url = f"{self.api_url}/logout"
                headers = {"Authorization": f"Bearer {self.token}"}
                
                response = self.session.post(logout_url, headers=headers, timeout=5)
                
            # Clear local session
            self.token = None
            self.user_id = None
            cache.delete('dmss_token')
            cache.delete('dmss_user_id')
            
            return True, "Logout successful"
            
        except Exception as e:
            return False, str(e)
    
    def is_logged_in(self):
        """Check if user is logged in"""
        token = cache.get('dmss_token') or self.token
        return token is not None
    
    def get_device_list(self):
        """Get list of devices from DMSS cloud"""
        if not self.is_logged_in():
            return [], "Not logged in"
        
        try:
            devices_url = f"{self.api_url}/device/list"
            headers = {"Authorization": f"Bearer {self.token}"}
            
            response = self.session.get(devices_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("code") == 0:
                    devices = result.get("data", {}).get("list", [])
                    self.devices = devices
                    
                    # Cache device list
                    cache.set('dmss_devices', devices, 300)  # 5 minutes
                    
                    return devices, "Success"
                else:
                    return [], result.get("msg", "Failed to get devices")
            else:
                return [], f"HTTP {response.status_code}"
                
        except Exception as e:
            return [], str(e)
    
    def get_device_info(self, device_id):
        """Get detailed information about a specific device"""
        if not self.is_logged_in():
            return None, "Not logged in"
        
        try:
            info_url = f"{self.api_url}/device/info"
            headers = {"Authorization": f"Bearer {self.token}"}
            
            params = {"deviceId": device_id}
            
            response = self.session.get(info_url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("code") == 0:
                    return result.get("data"), "Success"
                else:
                    return None, result.get("msg", "Failed to get device info")
            else:
                return None, f"HTTP {response.status_code}"
                
        except Exception as e:
            return None, str(e)
    
    def get_live_stream_url(self, device_id, channel=0):
        """Get live stream URL for device"""
        if not self.is_logged_in():
            return None, "Not logged in"
        
        try:
            stream_url = f"{self.api_url}/device/live/stream"
            headers = {"Authorization": f"Bearer {self.token}"}
            
            params = {
                "deviceId": device_id,
                "channel": channel,
                "streamType": "main"
            }
            
            response = self.session.get(stream_url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("code") == 0:
                    stream_data = result.get("data", {})
                    return stream_data.get("url"), "Success"
                else:
                    return None, result.get("msg", "Failed to get stream URL")
            else:
                return None, f"HTTP {response.status_code}"
                
        except Exception as e:
            return None, str(e)
    
    def get_device_snapshot(self, device_id, channel=0):
        """Get snapshot from device"""
        if not self.is_logged_in():
            return None, "Not logged in"
        
        try:
            snapshot_url = f"{self.api_url}/device/snapshot"
            headers = {"Authorization": f"Bearer {self.token}"}
            
            params = {
                "deviceId": device_id,
                "channel": channel
            }
            
            response = self.session.get(snapshot_url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                # Return image data
                return response.content, "Success"
            else:
                return None, f"HTTP {response.status_code}"
                
        except Exception as e:
            return None, str(e)
    
    def share_device(self, device_id, share_type="view"):
        """Share device with other users"""
        if not self.is_logged_in():
            return False, "Not logged in"
        
        try:
            share_url = f"{self.api_url}/device/share"
            headers = {"Authorization": f"Bearer {self.token}"}
            
            data = {
                "deviceId": device_id,
                "shareType": share_type,
                "duration": 86400  # 24 hours
            }
            
            response = self.session.post(share_url, headers=headers, json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("code") == 0:
                    return True, "Device shared successfully"
                else:
                    return False, result.get("msg", "Failed to share device")
            else:
                return False, f"HTTP {response.status_code}"
                
        except Exception as e:
            return False, str(e)
    
    def get_cloud_recordings(self, device_id, start_time=None, end_time=None):
        """Get cloud recordings for device"""
        if not self.is_logged_in():
            return [], "Not logged in"
        
        try:
            recordings_url = f"{self.api_url}/recordings/cloud"
            headers = {"Authorization": f"Bearer {self.token}"}
            
            params = {
                "deviceId": device_id,
                "startTime": start_time or int(time.time() - 86400),  # Last 24 hours
                "endTime": end_time or int(time.time())
            }
            
            response = self.session.get(recordings_url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("code") == 0:
                    return result.get("data", {}).get("list", []), "Success"
                else:
                    return [], result.get("msg", "Failed to get recordings")
            else:
                return [], f"HTTP {response.status_code}"
                
        except Exception as e:
            return [], str(e)


# Global DMSS client instance
dmss_client = DMSSClient()


def get_dmss_client():
    """Get global DMSS client instance"""
    return dmss_client


def authenticate_dmss(username, password):
    """Authenticate with DMSS and return client"""
    client = DMSSClient()
    success, message = client.login(username, password)
    
    if success:
        return client, "Login successful"
    else:
        return None, message


def get_dmss_devices():
    """Get devices from DMSS cloud"""
    client = get_dmss_client()
    
    if not client.is_logged_in():
        # Try to restore session from cache
        token = cache.get('dmss_token')
        user_id = cache.get('dmss_user_id')
        
        if token and user_id:
            client.token = token
            client.user_id = user_id
    
    return client.get_device_list()


def sync_dmss_devices_to_db():
    """Sync DMSS devices to local database"""
    from .models import CCTVDevice
    
    devices, message = get_dmss_devices()
    
    if not devices:
        return False, message
    
    synced_count = 0
    
    for device_data in devices:
        try:
            # Extract device information
            device_id = device_data.get('deviceId')
            name = device_data.get('name', f'DMSS-{device_id}')
            serial = device_data.get('serialNumber', device_id)
            
            # Create or update device
            device, created = CCTVDevice.objects.update_or_create(
                name=name,
                defaults={
                    'domain': serial,
                    'port': 37777,
                    'username': 'dmss',
                    'password': 'cloud',
                    'camera_count': device_data.get('channelCount', 4),
                    'status': 'online' if device_data.get('online') else 'offline'
                }
            )
            
            if created:
                synced_count += 1
                
        except Exception as e:
            print(f"Error syncing device {device_data}: {e}")
    
    return True, f"Synced {synced_count} devices"


if __name__ == "__main__":
    # Test DMSS connection
    client = DMSSClient()
    
    # Test login (replace with actual credentials)
    success, message = client.login("your_username", "your_password")
    print(f"Login: {success} - {message}")
    
    if success:
        devices, message = client.get_device_list()
        print(f"Devices: {len(devices)} found")
        
        for device in devices[:3]:  # Show first 3 devices
            print(f"  - {device.get('name')} ({device.get('deviceId')})")
