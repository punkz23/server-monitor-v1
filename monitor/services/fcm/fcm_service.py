import logging
import requests
import json
from django.conf import settings

logger = logging.getLogger(__name__)

class FcmService:
    """
    Service to handle Firebase Cloud Messaging push notifications
    """
    FCM_URL = "https://fcm.googleapis.com/fcm/send"
    
    def __init__(self):
        # In a real app, these would be in settings.py
        self.server_key = getattr(settings, 'FCM_SERVER_KEY', None)
        self.enabled = self.server_key is not None

    def send_push_notification(self, target_token, title, body, data=None):
        """
        Send a push notification to a specific device token
        """
        if not self.enabled:
            logger.info(f"FCM disabled. Would have sent: {title} - {body}")
            return False

        headers = {
            'Authorization': f'key={self.server_key}',
            'Content-Type': 'application/json',
        }

        payload = {
            'to': target_token,
            'notification': {
                'title': title,
                'body': body,
                'sound': 'default',
                'click_action': 'FLUTTER_NOTIFICATION_CLICK',
            },
            'data': data or {},
            'priority': 'high',
        }

        try:
            response = requests.post(
                self.FCM_URL,
                headers=headers,
                data=json.dumps(payload),
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Successfully sent FCM notification to {target_token}")
            return True
        except Exception as e:
            logger.error(f"Failed to send FCM notification: {e}")
            return False

    def send_to_topic(self, topic, title, body, data=None):
        """
        Send a notification to a specific topic (e.g., 'alerts')
        """
        return self.send_push_notification(f"/topics/{topic}", title, body, data)
