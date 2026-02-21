from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet
import base64

class EncryptedCharField(models.CharField):
    """
    A CharField that encrypts and decrypts its content transparently.
    Requires ENCRYPTION_KEY to be set in Django settings.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not hasattr(settings, 'ENCRYPTION_KEY'):
            raise RuntimeError("ENCRYPTION_KEY must be set in settings.py to use EncryptedCharField.")
        self.fernet = Fernet(base64.urlsafe_b64encode(settings.ENCRYPTION_KEY.encode('utf-8').ljust(32)[:32]))

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        try:
            return self.fernet.decrypt(value.encode('utf-8')).decode('utf-8')
        except Exception:
            # Handle cases where decryption might fail (e.g., key changed, invalid token)
            return value

    def to_python(self, value):
        if value is None:
            return value
        if isinstance(value, bytes):
            # If it's already bytes, it's likely encrypted, try to decrypt
            try:
                return self.fernet.decrypt(value).decode('utf-8')
            except Exception:
                return value.decode('utf-8') # Fallback if decryption fails, return as string
        return value # Already a string, return as is

    def get_prep_value(self, value):
        if value is None:
            return value
        # Ensure the value is a string before encryption
        if not isinstance(value, str):
            value = str(value)
        return self.fernet.encrypt(value.encode('utf-8')).decode('utf-8')

    def get_internal_type(self):
        return "CharField"
