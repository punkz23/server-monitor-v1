"""
SSH Credentials Management for Server Metrics Monitoring
Allows users to add/edit/delete SSH credentials for server monitoring
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import logging
import base64
from cryptography.fernet import Fernet
from django.conf import settings
import json

logger = logging.getLogger(__name__)


class SSHCredential(models.Model):
    """SSH credentials for server metrics monitoring"""
    
    ENCRYPTION_KEY = b'your-encryption-key-here-change-in-production'  # Should be moved to settings
    
    server = models.OneToOneField(
        'monitor.Server',
        on_delete=models.CASCADE,
        related_name='ssh_credential',
        help_text="Server this credential belongs to"
    )
    
    username = models.CharField(
        max_length=100,
        help_text="SSH username"
    )
    
    encrypted_password = models.TextField(
        help_text="Encrypted SSH password"
    )
    
    port = models.IntegerField(
        default=22,
        help_text="SSH port (default: 22)"
    )
    
    private_key_path = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Path to private key file (optional)"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this credential is active for monitoring"
    )
    
    last_tested = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time this credential was tested"
    )
    
    test_status = models.CharField(
        max_length=20,
        choices=[
            ('success', 'Connection Successful'),
            ('failed', 'Connection Failed'),
            ('not_tested', 'Not Tested')
        ],
        default='not_tested',
        help_text="Status of last connection test"
    )
    
    test_message = models.TextField(
        blank=True,
        help_text="Message from last connection test"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "SSH Credential"
        verbose_name_plural = "SSH Credentials"
        ordering = ['server__name']
    
    def __str__(self):
        return f"{self.server.name} - {self.username}"
    
    def set_password(self, password):
        """Encrypt and store password"""
        try:
            # Simple encryption - in production, use proper key management
            encoded = base64.b64encode(password.encode('utf-8')).decode('utf-8')
            self.encrypted_password = encoded
        except Exception as e:
            logger.error(f"Error encrypting password: {e}")
            raise ValidationError("Failed to encrypt password")
    
    def get_password(self):
        """Decrypt and return password"""
        try:
            decoded = base64.b64decode(self.encrypted_password.encode('utf-8')).decode('utf-8')
            return decoded
        except Exception as e:
            logger.error(f"Error decrypting password: {e}")
            return None
    
    def test_connection(self):
        """Test SSH connection with these credentials"""
        import paramiko
        
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            password = self.get_password()
            if not password:
                raise Exception("Could not decrypt password")
            
            ssh.connect(
                hostname=self.server.ip_address,
                port=self.port,
                username=self.username,
                password=password,
                timeout=10,
                allow_agent=False,
                look_for_keys=False
            )
            
            # Test basic command
            stdin, stdout, stderr = ssh.exec_command("echo 'Connection test successful'")
            result = stdout.read().decode().strip()
            
            ssh.close()
            
            if result == "Connection test successful":
                self.test_status = 'success'
                self.test_message = "Connection test successful"
                self.last_tested = timezone.now()
                self.save()
                return True, "Connection successful"
            else:
                self.test_status = 'failed'
                self.test_message = "Unexpected response from server"
                self.last_tested = timezone.now()
                self.save()
                return False, "Unexpected response"
                
        except Exception as e:
            self.test_status = 'failed'
            self.test_message = str(e)
            self.last_tested = timezone.now()
            self.save()
            return False, str(e)
    
    def clean(self):
        """Validate credential data"""
        if not self.username:
            raise ValidationError("Username is required")
        
        if not self.encrypted_password:
            raise ValidationError("Password is required")
        
        if self.port < 1 or self.port > 65535:
            raise ValidationError("Port must be between 1 and 65535")


class ServerMetricsConfig(models.Model):
    """Configuration for server metrics monitoring"""
    
    server = models.OneToOneField(
        'monitor.Server',
        on_delete=models.CASCADE,
        related_name='metrics_config',
        help_text="Server this configuration belongs to"
    )
    
    enable_cpu_monitoring = models.BooleanField(
        default=True,
        help_text="Enable CPU usage monitoring"
    )
    
    enable_ram_monitoring = models.BooleanField(
        default=True,
        help_text="Enable RAM usage monitoring"
    )
    
    enable_disk_monitoring = models.BooleanField(
        default=True,
        help_text="Enable disk usage monitoring"
    )
    
    enable_ssl_monitoring = models.BooleanField(
        default=True,
        help_text="Enable SSL certificate monitoring"
    )
    
    cpu_threshold_warning = models.FloatField(
        default=80.0,
        help_text="CPU usage warning threshold (%)"
    )
    
    cpu_threshold_critical = models.FloatField(
        default=95.0,
        help_text="CPU usage critical threshold (%)"
    )
    
    ram_threshold_warning = models.FloatField(
        default=80.0,
        help_text="RAM usage warning threshold (%)"
    )
    
    ram_threshold_critical = models.FloatField(
        default=95.0,
        help_text="RAM usage critical threshold (%)"
    )
    
    disk_threshold_warning = models.FloatField(
        default=80.0,
        help_text="Disk usage warning threshold (%)"
    )
    
    disk_threshold_critical = models.FloatField(
        default=95.0,
        help_text="Disk usage critical threshold (%)"
    )
    
    ssl_warning_days = models.IntegerField(
        default=30,
        help_text="SSL certificate warning threshold (days)"
    )
    
    ssl_critical_days = models.IntegerField(
        default=7,
        help_text="SSL certificate critical threshold (days)"
    )
    
    monitoring_interval = models.IntegerField(
        default=300,
        help_text="Monitoring interval in seconds"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether metrics monitoring is active"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Server Metrics Configuration"
        verbose_name_plural = "Server Metrics Configurations"
        ordering = ['server__name']
    
    def __str__(self):
        return f"{self.server.name} - Metrics Config"
    
    def clean(self):
        """Validate threshold values"""
        if self.cpu_threshold_warning >= self.cpu_threshold_critical:
            raise ValidationError("CPU warning threshold must be less than critical threshold")
        
        if self.ram_threshold_warning >= self.ram_threshold_critical:
            raise ValidationError("RAM warning threshold must be less than critical threshold")
        
        if self.disk_threshold_warning >= self.disk_threshold_critical:
            raise ValidationError("Disk warning threshold must be less than critical threshold")
        
        if self.ssl_critical_days >= self.ssl_warning_days:
            raise ValidationError("SSL critical days must be less than warning days")
