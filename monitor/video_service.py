"""
Video streaming service for CCTV cameras
Handles RTSP to WebRTC conversion and video streaming using Dahua RPC SDK
"""

import json
import subprocess
import threading
import time
import base64
from django.conf import settings
from django.core.cache import cache
from django.http import StreamingHttpResponse


class VideoStreamingService:
    """Service for handling CCTV video streaming with Dahua RPC"""
    
    def __init__(self):
        self.active_streams = {}
        
    def get_stream_info(self, device_id, camera_number):
        """Get streaming information for a camera using Dahua RPC or P2P"""
        from .models import CCTVDevice
        
        try:
            device = CCTVDevice.objects.get(id=device_id)
            
            # Check if device uses P2P (serial number instead of IP)
            if self.is_p2p_device(device.domain):
                print(f"Device {device.domain} is P2P - using P2P streaming")
                
                # Try P2P connection
                from .dahua_p2p import test_p2p_connection, get_p2p_rtsp_url
                
                p2p_result = test_p2p_connection(
                    device.domain,
                    device.username,
                    device.password
                )
                
                if p2p_result:
                    return {
                        'rtsp_url': get_p2p_rtsp_url(device.domain, device.username, device.password),
                        'device_name': device.name,
                        'camera_name': device.get_camera_name(camera_number),
                        'stream_key': f"device_{device_id}_cam_{camera_number}",
                        'status': 'online',
                        'connection_type': 'p2p',
                        'local_port': 8554
                    }
                else:
                    # Fallback to basic RTSP URL
                    return {
                        'rtsp_url': device.get_rtsp_url(camera_number),
                        'device_name': device.name,
                        'camera_name': device.get_camera_name(camera_number),
                        'stream_key': f"device_{device_id}_cam_{camera_number}",
                        'status': 'offline',
                        'connection_type': 'p2p_failed'
                    }
            else:
                # Use regular Dahua RPC for IP-based devices
                from .dahua_rpc import get_dahua_live_feed
                
                live_feed = get_dahua_live_feed(
                    device.domain, 
                    device.username, 
                    device.password, 
                    camera_number - 1
                )
                
                if live_feed:
                    return {
                        'rtsp_url': live_feed['stream_url'],
                        'device_name': device.name,
                        'camera_name': device.get_camera_name(camera_number),
                        'stream_key': f"device_{device_id}_cam_{camera_number}",
                        'status': live_feed['status'],
                        'snapshot': live_feed.get('snapshot'),
                        'camera_info': live_feed.get('camera_info'),
                        'live_frame': live_feed.get('live_frame'),
                        'connection_type': 'direct'
                    }
                else:
                    # Fallback to basic RTSP URL
                    return {
                        'rtsp_url': device.get_rtsp_url(camera_number),
                        'device_name': device.name,
                        'camera_name': device.get_camera_name(camera_number),
                        'stream_key': f"device_{device_id}_cam_{camera_number}",
                        'status': device.status,
                        'connection_type': 'direct_failed'
                    }
                
        except CCTVDevice.DoesNotExist:
            return None
    
    def is_p2p_device(self, domain):
        """Check if device domain is a P2P serial number"""
        # P2P serial numbers are typically 16-character alphanumeric strings
        if len(domain) == 16 and domain.replace('-', '').replace('_', '').isalnum():
            return True
        return False
    
    def get_live_snapshot(self, device_id, camera_number):
        """Get live snapshot from camera"""
        from .models import CCTVDevice
        
        try:
            device = CCTVDevice.objects.get(id=device_id)
            from .dahua_rpc import DahuaRpc
            
            dahua = DahuaRpc(device.domain, device.username, device.password)
            
            if dahua.login():
                snapshot = dahua.get_snapshot(camera_number - 1)
                dahua.logout()
                
                if snapshot:
                    # Convert to base64 for web display
                    snapshot_b64 = base64.b64encode(snapshot).decode('utf-8')
                    return f"data:image/jpeg;base64,{snapshot_b64}"
                    
        except Exception as e:
            print(f"Snapshot error: {e}")
            
        return None
    
    def get_mjpeg_stream(self, device_id, camera_number):
        """Get MJPEG stream from camera"""
        from .models import CCTVDevice
        
        try:
            device = CCTVDevice.objects.get(id=device_id)
            from .dahua_rpc import DahuaRpc
            
            dahua = DahuaRpc(device.domain, device.username, device.password)
            
            if dahua.login():
                live_frame = dahua.get_live_frame(camera_number - 1)
                dahua.logout()
                
                if live_frame:
                    return live_frame
                    
        except Exception as e:
            print(f"MJPEG stream error: {e}")
            
        return None
    
    def stream_mjpeg_response(self, device_id, camera_number):
        """Create MJPEG streaming response"""
        def generate_frames():
            from .dahua_rpc import DahuaRpc
            from .models import CCTVDevice
            
            device = CCTVDevice.objects.get(id=device_id)
            dahua = DahuaRpc(device.domain, device.username, device.password)
            
            if dahua.login():
                try:
                    # MJPEG boundary
                    boundary = "--frame"
                    
                    while True:
                        try:
                            # Get snapshot
                            snapshot = dahua.get_snapshot(camera_number - 1)
                            
                            if snapshot:
                                yield (b'--frame\r\n'
                                       b'Content-Type: image/jpeg\r\n\r\n' + snapshot + b'\r\n')
                            else:
                                # Send error frame
                                yield (b'--frame\r\n'
                                       b'Content-Type: image/jpeg\r\n\r\n' + b'' + b'\r\n')
                            
                            time.sleep(0.1)  # 10 FPS
                            
                        except Exception as e:
                            print(f"Frame generation error: {e}")
                            break
                            
                finally:
                    dahua.logout()
            else:
                # Send error frame
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + b'' + b'\r\n')
        
        return StreamingHttpResponse(
            generate_frames(),
            content_type="multipart/x-mixed-replace; boundary=frame"
        )
    
    def test_camera_connection(self, device_id, camera_number):
        """Test connection to specific camera"""
        from .models import CCTVDevice
        
        try:
            device = CCTVDevice.objects.get(id=device_id)
            from .dahua_rpc import test_dahua_connection
            
            return test_dahua_connection(
                device.domain,
                device.username,
                device.password
            )
            
        except Exception as e:
            print(f"Connection test error: {e}")
            return False


def get_video_player_html(rtsp_url, device_name, camera_name):
    """Generate HTML for video player"""
    
    # Try multiple player options
    players = {
        'hls': get_hls_player(rtsp_url, device_name, camera_name),
        'webrtc': get_webrtc_player(rtsp_url, device_name, camera_name),
        'rtsp': get_rtsp_player(rtsp_url, device_name, camera_name),
        'fallback': get_fallback_player(rtsp_url, device_name, camera_name)
    }
    
    return players


def get_hls_player(rtsp_url, device_name, camera_name):
    """HLS video player (requires FFmpeg conversion)"""
    return f"""
    <div class="video-player hls-player" data-rtsp="{rtsp_url}">
        <video id="hls-video" controls autoplay muted style="width: 100%; height: 100%;">
            <source src="/media/streams/device_1_cam_1.m3u8" type="application/x-mpegURL">
            Your browser does not support HLS video.
        </video>
        <div class="player-overlay">
            <div class="player-info">
                <h4>{device_name}</h4>
                <p>{camera_name}</p>
                <p style="font-size: 0.8rem; color: #888;">HLS Stream</p>
            </div>
        </div>
    </div>
    """


def get_webrtc_player(rtsp_url, device_name, camera_name):
    """WebRTC video player (requires WebRTC server)"""
    return f"""
    <div class="video-player webrtc-player" data-rtsp="{rtsp_url}">
        <video id="webrtc-video" autoplay muted style="width: 100%; height: 100%;"></video>
        <div class="player-overlay">
            <div class="player-info">
                <h4>{device_name}</h4>
                <p>{camera_name}</p>
                <p style="font-size: 0.8rem; color: #888;">WebRTC Stream</p>
            </div>
        </div>
        <script>
            // WebRTC connection would be established here
            // This requires a WebRTC signaling server
            console.log('WebRTC player for: {rtsp_url}');
        </script>
    </div>
    """


def get_rtsp_player(rtsp_url, device_name, camera_name):
    """RTSP player (requires browser plugin)"""
    return f"""
    <div class="video-player rtsp-player" data-rtsp="{rtsp_url}">
        <object type="application/x-rtsp" data="{rtsp_url}" width="100%" height="100%">
            <param name="autoplay" value="true">
            <param name="controls" value="true">
            <embed src="{rtsp_url}" type="application/x-rtsp" width="100%" height="100%" autoplay="true" controls="true">
        </object>
        <div class="player-overlay">
            <div class="player-info">
                <h4>{device_name}</h4>
                <p>{camera_name}</p>
                <p style="font-size: 0.8rem; color: #888;">RTSP (requires plugin)</p>
            </div>
        </div>
    </div>
    """


def get_fallback_player(rtsp_url, device_name, camera_name):
    """Fallback player with RTSP URL and instructions"""
    return f"""
    <div class="video-player fallback-player" data-rtsp="{rtsp_url}">
        <div class="fallback-content">
            <div class="camera-icon">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="2" y="4" width="20" height="16" rx="2"/>
                    <circle cx="8" cy="10" r="2"/>
                    <path d="M14 10l4 4-4 4"/>
                </svg>
            </div>
            <h3>{camera_name}</h3>
            <p style="color: #888; margin: 8px 0;">Live Camera Feed</p>
            
            <div class="rtsp-info">
                <p style="font-size: 0.8rem; margin-bottom: 8px;">RTSP Stream URL:</p>
                <code style="background: #f5f5f5; padding: 8px; border-radius: 4px; display: block; font-size: 0.7rem; word-break: break-all;">
                    {rtsp_url}
                </code>
            </div>
            
            <div class="player-actions" style="margin-top: 16px;">
                <button onclick="copyRTSP('{rtsp_url}')" class="btn btn-primary">Copy RTSP URL</button>
                <button onclick="openVLC('{rtsp_url}')" class="btn btn-secondary">Open in VLC</button>
                <button onclick="startStream()" class="btn btn-secondary">Start Web Stream</button>
            </div>
            
            <div class="stream-instructions" style="margin-top: 16px; font-size: 0.8rem; color: #666;">
                <p><strong>To view this camera:</strong></p>
                <ul style="margin: 8px 0; padding-left: 20px;">
                    <li>Use VLC Media Player: File → Open Network Stream</li>
                    <li>Use any RTSP-compatible player</li>
                    <li>Copy URL to mobile apps like VLC or iSpy</li>
                    <li>Configure media server for web viewing</li>
                </ul>
            </div>
        </div>
    </div>
    """


def generate_stream_config(rtsp_url):
    """Generate streaming configuration"""
    return {
        'rtsp_url': rtsp_url,
        'hls_url': f"/media/streams/{hash(rtsp_url) % 10000}.m3u8",
        'webrtc_url': f"webrtc://stream/{hash(rtsp_url) % 10000}",
        'stream_key': f"stream_{hash(rtsp_url) % 10000}"
    }
