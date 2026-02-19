import logging
from typing import List, Dict, Any
from django.conf import settings
from django.core.mail import send_mail
from .fcm.fcm_service import FcmService

logger = logging.getLogger(__name__)

class NotificationChannel:
    """Base class for notification channels."""
    def send(self, recipient: str, subject: str, message: str) -> bool:
        raise NotImplementedError

class EmailChannel(NotificationChannel):
    """Email notification channel."""
    def send(self, recipient: str, subject: str, message: str) -> bool:
        try:
            # In a real app, you'd use send_mail
            # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient])
            logger.info(f"Sending email to {recipient}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

class ConsoleChannel(NotificationChannel):
    """Console notification channel for development/debugging."""
    def send(self, recipient: str, subject: str, message: str) -> bool:
        print(f"[{recipient}] {subject}: {message}")
        logger.info(f"Console notification to {recipient}: {subject}")
        return True

class PushNotificationChannel(NotificationChannel):
    """Mobile Push notification channel via FCM."""
    def __init__(self):
        self.fcm = FcmService()

    def send(self, recipient: str, subject: str, message: str) -> bool:
        # In a topic-based system, we might broadcast to 'all_users' or a specific recipient ID
        # For simplicity, we'll send to the 'alerts' topic which mobile apps can subscribe to
        topic = "alerts"
        return self.fcm.send_to_topic(topic, subject, message)

class NotificationService:
    """Service to handle sending notifications via configured channels."""
    
    def __init__(self):
        self.channels: Dict[str, NotificationChannel] = {
            'email': EmailChannel(),
            'console': ConsoleChannel(),
            'push': PushNotificationChannel(),
        }

    def send_notification(self, channels: List[str], recipient: str, subject: str, message: str):
        """
        Send a notification to the specified channels.
        
        Args:
            channels: List of channel names ('email', 'console', etc.)
            recipient: The recipient identifier (email address, user ID, etc.)
            subject: The notification subject
            message: The notification body
        """
        results = {}
        for channel_name in channels:
            channel = self.channels.get(channel_name)
            if channel:
                success = channel.send(recipient, subject, message)
                results[channel_name] = success
            else:
                logger.warning(f"Notification channel '{channel_name}' not found.")
                results[channel_name] = False
        return results
