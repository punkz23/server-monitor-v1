from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

class ServerMetrics(models.Model):
    """
    Detailed server metrics collected by agents
    """
    server = models.ForeignKey(
        'Server',
        on_delete=models.CASCADE,
        related_name='metrics',
        help_text="Server this metrics belong to"
    )
    
    timestamp = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When these metrics were collected"
    )
    
    # Agent identification
    agent_server_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Server ID from agent"
    )
    
    # CPU Metrics
    cpu_percent = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="CPU usage percentage"
    )
    
    cpu_count = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Number of CPU cores"
    )
    
    load_1m = models.FloatField(
        null=True,
        blank=True,
        help_text="1-minute load average"
    )
    
    load_5m = models.FloatField(
        null=True,
        blank=True,
        help_text="5-minute load average"
    )
    
    load_15m = models.FloatField(
        null=True,
        blank=True,
        help_text="15-minute load average"
    )
    
    # Memory Metrics
    memory_total = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Total memory in bytes"
    )
    
    memory_used = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Used memory in bytes"
    )
    
    memory_percent = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Memory usage percentage"
    )
    
    # Disk Metrics
    disk_total = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Total disk space in bytes"
    )
    
    disk_used = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Used disk space in bytes"
    )
    
    disk_percent = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Disk usage percentage"
    )
    
    # Network Metrics
    network_bytes_sent = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Total bytes sent"
    )
    
    network_bytes_recv = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Total bytes received"
    )
    
    network_packets_sent = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Total packets sent"
    )
    
    network_packets_recv = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Total packets received"
    )
    
    # System Metrics
    uptime_seconds = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="System uptime in seconds"
    )
    
    process_count = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Number of running processes"
    )
    
    hostname = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="System hostname"
    )
    
    # Directory Metrics
    directory_metrics = models.JSONField(
        null=True,
        blank=True,
        help_text="Detailed metrics for monitored directories (file count, size, status)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Server Metrics"
        verbose_name_plural = "Server Metrics"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['server', 'timestamp']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['agent_server_id', 'timestamp']),
            models.Index(fields=['server', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.server.name} - {self.timestamp}"
    
    @property
    def memory_gb(self):
        """Memory in GB"""
        if self.memory_total:
            return round(self.memory_total / (1024**3), 2)
        return None
    
    @property
    def memory_used_gb(self):
        """Used memory in GB"""
        if self.memory_used:
            return round(self.memory_used / (1024**3), 2)
        return None
    
    @property
    def disk_gb(self):
        """Disk space in GB"""
        if self.disk_total:
            return round(self.disk_total / (1024**3), 2)
        return None
    
    @property
    def disk_used_gb(self):
        """Used disk space in GB"""
        if self.disk_used:
            return round(self.disk_used / (1024**3), 2)
        return None
    
    @property
    def uptime_days(self):
        """Uptime in days"""
        if self.uptime_seconds:
            return round(self.uptime_seconds / 86400, 2)
        return None
    
    @property
    def network_gb_sent(self):
        """Network sent in GB"""
        if self.network_bytes_sent:
            return round(self.network_bytes_sent / (1024**3), 2)
        return None
    
    @property
    def network_gb_recv(self):
        """Network received in GB"""
        if self.network_bytes_recv:
            return round(self.network_bytes_recv / (1024**3), 2)
        return None
