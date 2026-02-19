import secrets
import re
import socket
import time
import requests
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from ipaddress import ip_address, ip_network


class NetworkDevice(models.Model):
    """Model for network devices like firewalls, switches, routers, PCs, mobiles, printers, APs"""
    TYPE_FIREWALL = "FIREWALL"
    TYPE_SWITCH = "SWITCH"
    TYPE_ROUTER = "ROUTER"
    TYPE_PC = "PC"
    TYPE_MOBILE = "MOBILE"
    TYPE_PRINTER = "PRINTER"
    TYPE_ACCESS_POINT = "ACCESS_POINT"
    TYPE_UNKNOWN = "UNKNOWN"
    
    TYPE_CHOICES = [
        (TYPE_FIREWALL, "Firewall"),
        (TYPE_SWITCH, "Switch"),
        (TYPE_ROUTER, "Router"),
        (TYPE_PC, "PC/Computer"),
        (TYPE_MOBILE, "Mobile Phone"),
        (TYPE_PRINTER, "Printer"),
        (TYPE_ACCESS_POINT, "Access Point"),
        (TYPE_UNKNOWN, "Unknown"),
    ]
    
    name = models.CharField(max_length=200, unique=True)
    device_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_UNKNOWN)
    ip_address = models.GenericIPAddressField(protocol="IPv4")
    mac_address = models.CharField(max_length=17, blank=True, null=True, help_text="MAC address in format XX:XX:XX:XX:XX:XX")
    vendor = models.CharField(max_length=100, blank=True, null=True, help_text="Device vendor identified from MAC address")
    hostname = models.CharField(max_length=255, blank=True, null=True, help_text="Hostname resolved from IP")
    os_fingerprint = models.CharField(max_length=100, blank=True, null=True, help_text="Operating system fingerprint")
    open_ports = models.JSONField(default=dict, blank=True, help_text="Open ports and services")
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, help_text="Device is currently active on network")
    auto_discovered = models.BooleanField(default=True, help_text="Automatically discovered via network scan")
    notes = models.TextField(blank=True, null=True)
    network = models.CharField(max_length=100, blank=True, null=True, help_text="Network segment or subnet (e.g., 172.10.10.0/24)")
    
    # Existing SNMP and API fields
    snmp_community = models.CharField(max_length=100, default="public")
    snmp_port = models.PositiveIntegerField(default=161)
    api_token = models.CharField(max_length=255, blank=True, null=True)
    api_port = models.PositiveIntegerField(default=443)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_checked = models.DateTimeField(null=True, blank=True)
    
    api_username = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Username for API authentication. Must be 3-100 characters long and contain only letters, numbers, and underscores.",
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9_]{3,100}$',
                message='Username must be 3-100 characters and contain only letters, numbers, and underscores.'
            )
        ]
    )
    api_port = models.PositiveIntegerField(
        default=443,
        validators=[
            MinValueValidator(1, message="Port must be at least 1"),
            MaxValueValidator(65535, message="Port cannot exceed 65535")
        ]
    )
    
    def clean(self):
        """Validate the model before saving"""
        super().clean()
        
        # Auto-determine network if not set
        if not self.network and self.ip_address:
            self.network = self.get_network_from_ip(self.ip_address)
        
        # Require API username if API token is provided
        if self.api_token and not self.api_username:
            raise ValidationError({
                'api_username': 'API username is required when API token is provided'
            })
            
        # Require SNMP community if SNMP port is set
        if self.snmp_port and not self.snmp_community:
            raise ValidationError({
                'snmp_community': 'SNMP community is required when SNMP port is specified'
            })
    
    @staticmethod
    def get_network_from_ip(ip_addr):
        """Determine network segment from IP address"""
        try:
            ip = ip_address(ip_addr)
            
            # Define common network segments
            if ip in ip_network('192.168.1.0/24'):
                return '192.168.1.0/24'
            elif ip in ip_network('192.168.253.0/24'):
                return '192.168.253.0/24'
            elif ip in ip_network('192.168.254.0/24'):
                return '192.168.254.0/24'
            elif ip in ip_network('192.168.56.0/24'):
                return '192.168.56.0/24'
            elif ip in ip_network('172.10.10.0/24'):
                return '172.10.10.0/24'
            elif ip in ip_network('10.0.0.0/24'):
                return '10.0.0.0/24'
            elif ip in ip_network('172.16.0.0/24'):
                return '172.16.0.0/24'
            else:
                # Determine class-based network
                if ip.version == 4:
                    if ip.is_private:
                        if ip.packed[0] == 10:
                            return '10.0.0.0/8'
                        elif ip.packed[0:2] == b'\xac\x10':  # 172.16-31
                            return '172.16.0.0/12'
                        elif ip.packed[0:2] == b'\xc0\xa8':  # 192.168
                            # Check for specific subnets first
                            if ip.packed[2] == 1:
                                return '192.168.1.0/24'
                            elif ip.packed[2] == 253:
                                return '192.168.253.0/24'
                            elif ip.packed[2] == 254:
                                return '192.168.254.0/24'
                            elif ip.packed[2] == 56:
                                return '192.168.56.0/24'
                            else:
                                return '192.168.0.0/16'
                
                return f"{ip_addr}/32"  # Single host
        except Exception:
            return f"{ip_addr}/32"  # Fallback to single host
    
    def save(self, *args, **kwargs):
        """Override save to auto-determine network"""
        if not self.network and self.ip_address:
            self.network = self.get_network_from_ip(self.ip_address)
        super().save(*args, **kwargs)


class NetworkMetric(models.Model):
    """Time series metrics for network devices"""
    device = models.ForeignKey(NetworkDevice, on_delete=models.CASCADE, related_name='metrics')
    metric_name = models.CharField(max_length=100)  # cpu_usage, memory_usage, bandwidth_in, etc.
    value = models.FloatField()
    unit = models.CharField(max_length=20)  # %, Mbps, packets/sec, etc.
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['device', 'metric_name', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.device.name} - {self.metric_name}: {self.value}{self.unit}"


class NetworkInterface(models.Model):
    """Network interfaces on devices"""
    device = models.ForeignKey(NetworkDevice, on_delete=models.CASCADE, related_name='interfaces')
    name = models.CharField(max_length=100)  # eth0, wan1, etc.
    description = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, default='unknown')  # up, down, unknown
    speed = models.IntegerField(null=True, blank=True)  # Mbps
    mtu = models.IntegerField(null=True, blank=True)
    username = models.CharField(max_length=50, default="admin")
    password = models.CharField(max_length=50, default="admin123456")
    
    def __str__(self):
        return f"{self.device.name} - {self.name}"


class SecurityEvent(models.Model):
    """Security events from firewall"""
    device = models.ForeignKey(NetworkDevice, on_delete=models.CASCADE, related_name='security_events')
    event_type = models.CharField(max_length=100)  # blocked, allowed, alert, etc.
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    dest_ip = models.GenericIPAddressField(null=True, blank=True)
    source_port = models.IntegerField(null=True, blank=True)
    dest_port = models.IntegerField(null=True, blank=True)
    protocol = models.CharField(max_length=10, blank=True)  # TCP, UDP, ICMP
    action = models.CharField(max_length=20)  # allow, deny, drop
    rule_name = models.CharField(max_length=200, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    severity = models.CharField(max_length=20, default='medium')  # low, medium, high, critical
    
    class Meta:
        indexes = [
            models.Index(fields=['device', 'timestamp']),
            models.Index(fields=['event_type', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.device.name} - {self.event_type} from {self.source_ip}"


class TrafficLog(models.Model):
    """Traffic statistics for interfaces"""
    interface = models.ForeignKey(NetworkInterface, on_delete=models.CASCADE, related_name='traffic_logs')
    bytes_in = models.IntegerField(default=0)
    bytes_out = models.IntegerField(default=0)
    packets_in = models.IntegerField(default=0)
    packets_out = models.IntegerField(default=0)
    errors_in = models.IntegerField(default=0)
    errors_out = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['interface', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.interface.device.name} - {self.interface.name} traffic"


class DeviceBandwidthUsage(models.Model):
    """Per-device bandwidth usage statistics"""
    device = models.ForeignKey(NetworkDevice, on_delete=models.CASCADE, related_name='bandwidth_usage')
    source_ip = models.GenericIPAddressField(help_text="Source IP address")
    dest_ip = models.GenericIPAddressField(help_text="Destination IP address")
    bytes_sent = models.BigIntegerField(default=0, help_text="Total bytes sent from this IP")
    bytes_received = models.BigIntegerField(default=0, help_text="Total bytes received by this IP")
    packets_sent = models.IntegerField(default=0, help_text="Total packets sent from this IP")
    packets_received = models.IntegerField(default=0, help_text="Total packets received by this IP")
    connections = models.IntegerField(default=0, help_text="Number of connections")
    protocols = models.JSONField(default=list, help_text="List of protocols used")
    first_seen = models.DateTimeField(auto_now_add=True, help_text="First time this IP was seen")
    last_seen = models.DateTimeField(auto_now=True, help_text="Last time this IP was active")
    
    class Meta:
        indexes = [
            models.Index(fields=['device', 'source_ip', 'last_seen']),
            models.Index(fields=['device', 'dest_ip', 'last_seen']),
            models.Index(fields=['last_seen']),
        ]
        unique_together = ['device', 'source_ip', 'dest_ip']
    
    def __str__(self):
        return f"{self.device.name} - {self.source_ip} -> {self.dest_ip}"
    
    @property
    def total_bytes(self):
        """Total bytes transferred (sent + received)"""
        return self.bytes_sent + self.bytes_received
    
    @property
    def total_packets(self):
        """Total packets transferred (sent + received)"""
        return self.packets_sent + self.packets_received


class Server(models.Model):
    STATUS_UNKNOWN = "UNKNOWN"
    STATUS_UP = "UP"
    STATUS_DOWN = "DOWN"

    TYPE_WEB = "WEB"
    TYPE_DB = "DB"
    TYPE_FILE = "FILE"
    TYPE_DEV = "DEV"
    TYPE_OTHER = "OTHER"

    STATUS_CHOICES = [
        (STATUS_UNKNOWN, "Unknown"),
        (STATUS_UP, "Up"),
        (STATUS_DOWN, "Down"),
    ]

    TYPE_CHOICES = [
        (TYPE_WEB, "Web server"),
        (TYPE_DB, "DB server"),
        (TYPE_FILE, "File server"),
        (TYPE_DEV, "Development server"),
        (TYPE_OTHER, "Other"),
    ]

    name = models.CharField(max_length=200, unique=True)
    agent_token = models.CharField(
        max_length=128,
        unique=True,
        null=True,
        blank=True,
        editable=False,
    )
    server_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=TYPE_WEB,
    )
    ip_address = models.GenericIPAddressField(protocol="IPv4")
    port = models.PositiveIntegerField(default=80)
    use_https = models.BooleanField(default=False)
    path = models.CharField(max_length=200, default="/")
    http_check = models.BooleanField(default=True)
    enabled = models.BooleanField(default=True)

    pinned = models.BooleanField(default=False)
    tags = models.CharField(max_length=500, blank=True, default="")

    last_status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_UNKNOWN,
    )

    last_http_ok = models.BooleanField(null=True, blank=True)
    skip_ssl_verification = models.BooleanField(default=False, help_text="Skip SSL certificate verification for HTTPS checks")

    last_checked = models.DateTimeField(null=True, blank=True)
    last_latency_ms = models.PositiveIntegerField(null=True, blank=True)
    last_http_status_code = models.PositiveIntegerField(null=True, blank=True)
    last_error = models.TextField(blank=True, default="")

    last_resource_checked = models.DateTimeField(null=True, blank=True)
    last_cpu_percent = models.FloatField(null=True, blank=True)
    last_ram_percent = models.FloatField(null=True, blank=True)
    last_disk_percent = models.FloatField(null=True, blank=True)
    last_load_1 = models.FloatField(null=True, blank=True)
    last_uptime_seconds = models.BigIntegerField(null=True, blank=True)
    last_boot_time = models.DateTimeField(null=True, blank=True)

    last_db_checked = models.DateTimeField(null=True, blank=True)
    last_db_process_up = models.BooleanField(null=True, blank=True)
    last_db_port_ok = models.BooleanField(null=True, blank=True)
    last_db_connect_ok = models.BooleanField(null=True, blank=True)
    last_db_ping_ms = models.FloatField(null=True, blank=True)
    last_db_connections = models.IntegerField(null=True, blank=True)
    last_db_max_connections = models.IntegerField(null=True, blank=True)
    last_db_conn_usage_percent = models.FloatField(null=True, blank=True)
    last_db_qps = models.FloatField(null=True, blank=True)
    last_db_read_qps = models.FloatField(null=True, blank=True)
    last_db_write_qps = models.FloatField(null=True, blank=True)
    last_db_tps = models.FloatField(null=True, blank=True)
    last_db_avg_query_ms = models.FloatField(null=True, blank=True)
    last_db_p95_query_ms = models.FloatField(null=True, blank=True)
    last_db_p99_query_ms = models.FloatField(null=True, blank=True)
    last_db_slow_1m = models.IntegerField(null=True, blank=True)

    # Agent-related fields
    agent_status = models.CharField(
        max_length=20,
        choices=[
            ('online', 'Online'),
            ('offline', 'Offline'),
            ('unknown', 'Unknown'),
            ('error', 'Error'),
        ],
        default='unknown',
        help_text="Agent status"
    )
    
    agent_version = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Agent version"
    )
    
    last_agent_heartbeat = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last heartbeat from agent"
    )
    
    last_agent_metrics = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last metrics received from agent"
    )
    
    agent_token = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        unique=True,
        help_text="Agent authentication token"
    )

    monitored_directories = models.TextField(
        blank=True,
        default="/var/www/html,/home/user/logs",
        help_text="Comma-separated list of directories to monitor"
    )

    ssl_cert_path = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Path to SSL certificate file on the server (for SSH-based monitoring)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Server"
        verbose_name_plural = "Servers"
        ordering = ["-pinned", "name"]
        indexes = [
            models.Index(fields=["server_type"]),
            models.Index(fields=["ip_address"]),
            models.Index(fields=["server_type", "ip_address"]),
            models.Index(fields=["server_type", "-pinned", "name"]),
            models.Index(fields=["enabled", "server_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.ip_address})"

    def save(self, *args, **kwargs):
        if not self.agent_token:
            for _ in range(10):
                token = secrets.token_urlsafe(32)
                if not type(self).objects.filter(agent_token=token).exists():
                    self.agent_token = token
                    break
        return super().save(*args, **kwargs)


class CheckResult(models.Model):
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name="checks")
    checked_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=Server.STATUS_CHOICES)
    http_ok = models.BooleanField(null=True, blank=True)
    latency_ms = models.PositiveIntegerField(null=True, blank=True)
    http_status_code = models.PositiveIntegerField(null=True, blank=True)
    error = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-checked_at"]

    def __str__(self) -> str:
        return f"{self.server.name} @ {self.checked_at} = {self.status}"


class ResourceSample(models.Model):
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name="resource_samples")
    collected_at = models.DateTimeField()

    cpu_percent = models.FloatField(null=True, blank=True)
    load_1 = models.FloatField(null=True, blank=True)
    load_5 = models.FloatField(null=True, blank=True)
    load_15 = models.FloatField(null=True, blank=True)

    ram_total_bytes = models.BigIntegerField(null=True, blank=True)
    ram_used_bytes = models.BigIntegerField(null=True, blank=True)
    ram_percent = models.FloatField(null=True, blank=True)

    boot_time = models.DateTimeField(null=True, blank=True)
    uptime_seconds = models.BigIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-collected_at"]
        indexes = [
            models.Index(fields=["server", "collected_at"]),
            models.Index(fields=["collected_at"]),
        ]


class AlertRule(models.Model):
    KIND_SERVER_DOWN = "server_down"
    KIND_HTTP_UNHEALTHY = "http_unhealthy"
    KIND_AGENT_STALE = "agent_stale"
    KIND_DB_CONNECT_FAIL = "db_connect_fail"
    KIND_CPU_HIGH = "cpu_high"
    KIND_RAM_HIGH = "ram_high"
    KIND_DB_CONN_HIGH = "db_conn_high"

    SEVERITY_INFO = "INFO"
    SEVERITY_WARN = "WARN"
    SEVERITY_CRIT = "CRIT"

    KIND_CHOICES = [
        (KIND_SERVER_DOWN, "Server down"),
        (KIND_HTTP_UNHEALTHY, "HTTP unhealthy"),
        (KIND_AGENT_STALE, "Agent stale"),
        (KIND_DB_CONNECT_FAIL, "DB connect failed"),
        (KIND_CPU_HIGH, "CPU high"),
        (KIND_RAM_HIGH, "RAM high"),
        (KIND_DB_CONN_HIGH, "DB connection usage high"),
    ]

    SEVERITY_CHOICES = [
        (SEVERITY_INFO, "Info"),
        (SEVERITY_WARN, "Warning"),
        (SEVERITY_CRIT, "Critical"),
    ]

    name = models.CharField(max_length=200)
    enabled = models.BooleanField(default=True)
    kind = models.CharField(max_length=50, choices=KIND_CHOICES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default=SEVERITY_WARN)

    threshold = models.FloatField(null=True, blank=True)
    duration_seconds = models.IntegerField(default=0)

    tags_filter = models.CharField(max_length=500, blank=True, default="")
    pinned_only = models.BooleanField(default=False)
    
    notification_channels = models.JSONField(default=list, blank=True, help_text="List of notification channels (e.g. ['email', 'console'])")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["enabled", "kind"]) ]

    def __str__(self) -> str:
        return self.name


class AlertState(models.Model):
    rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE, related_name="states")
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name="alert_states")

    is_active = models.BooleanField(default=False)
    pending_since = models.DateTimeField(null=True, blank=True)
    active_since = models.DateTimeField(null=True, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("rule", "server")]
        indexes = [models.Index(fields=["server", "is_active"])]


class AlertEvent(models.Model):
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name="alert_events", null=True, blank=True)
    rule = models.ForeignKey(AlertRule, on_delete=models.SET_NULL, null=True, blank=True, related_name="events")

    created_at = models.DateTimeField(auto_now_add=True)
    kind = models.CharField(max_length=50, blank=True, default="")
    severity = models.CharField(max_length=10, choices=AlertRule.SEVERITY_CHOICES, default=AlertRule.SEVERITY_INFO)
    is_recovery = models.BooleanField(default=False)

    title = models.CharField(max_length=200, blank=True, default="")
    message = models.TextField(blank=True, default="")
    value = models.FloatField(null=True, blank=True)
    payload = models.JSONField(blank=True, default=dict)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["created_at"]), models.Index(fields=["server", "created_at"]) ]


class DiskUsageSample(models.Model):
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name="disk_usage_samples")
    collected_at = models.DateTimeField()
    mount = models.CharField(max_length=200)
    fstype = models.CharField(max_length=64, blank=True, default="")
    total_bytes = models.BigIntegerField(null=True, blank=True)
    used_bytes = models.BigIntegerField(null=True, blank=True)
    percent = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ["-collected_at"]
        indexes = [models.Index(fields=["server", "collected_at"])]


class DiskIOSample(models.Model):
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name="disk_io_samples")
    collected_at = models.DateTimeField()
    read_bytes = models.BigIntegerField(null=True, blank=True)
    write_bytes = models.BigIntegerField(null=True, blank=True)
    read_time_ms = models.BigIntegerField(null=True, blank=True)
    write_time_ms = models.BigIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-collected_at"]
        indexes = [models.Index(fields=["server", "collected_at"])]


class NetworkSample(models.Model):
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name="network_samples")
    collected_at = models.DateTimeField()
    bytes_sent = models.BigIntegerField(null=True, blank=True)
    bytes_recv = models.BigIntegerField(null=True, blank=True)
    packets_sent = models.BigIntegerField(null=True, blank=True)
    packets_recv = models.BigIntegerField(null=True, blank=True)
    errin = models.BigIntegerField(null=True, blank=True)
    errout = models.BigIntegerField(null=True, blank=True)
    dropin = models.BigIntegerField(null=True, blank=True)
    dropout = models.BigIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-collected_at"]
        indexes = [models.Index(fields=["server", "collected_at"])]


class RebootEvent(models.Model):
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name="reboot_events")
    boot_time = models.DateTimeField()
    detected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-boot_time"]
        indexes = [models.Index(fields=["server", "boot_time"])]


class DbSample(models.Model):
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name="db_samples")
    collected_at = models.DateTimeField()

    engine = models.CharField(max_length=20, blank=True, default="")

    process_up = models.BooleanField(null=True, blank=True)
    port_ok = models.BooleanField(null=True, blank=True)
    port_ms = models.FloatField(null=True, blank=True)
    connect_ok = models.BooleanField(null=True, blank=True)
    ping_ms = models.FloatField(null=True, blank=True)

    current_connections = models.IntegerField(null=True, blank=True)
    max_connections = models.IntegerField(null=True, blank=True)
    connection_usage_percent = models.FloatField(null=True, blank=True)

    qps = models.FloatField(null=True, blank=True)
    read_qps = models.FloatField(null=True, blank=True)
    write_qps = models.FloatField(null=True, blank=True)
    tps = models.FloatField(null=True, blank=True)

    avg_query_ms = models.FloatField(null=True, blank=True)
    p95_query_ms = models.FloatField(null=True, blank=True)
    p99_query_ms = models.FloatField(null=True, blank=True)
    slow_queries_1m = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-collected_at"]
        indexes = [models.Index(fields=["server", "collected_at"])]


class ISPConnection(models.Model):
    ISP_CONVERGE = "CONVERGE"
    ISP_PLDT = "PLDT"
    
    ISP_CHOICES = [
        (ISP_CONVERGE, "Converge ICT"),
        (ISP_PLDT, "PLDT"),
    ]
    
    name = models.CharField(max_length=100)
    isp_type = models.CharField(max_length=20, choices=ISP_CHOICES)
    gateway_ip = models.GenericIPAddressField()
    dns_servers = models.TextField(help_text="Comma-separated DNS IPs")
    bandwidth_mbps = models.IntegerField()
    primary_connection = models.BooleanField(default=False)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_checked = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "ISP Connection"
        verbose_name_plural = "ISP Connections"
        ordering = ["-primary_connection", "name"]
    
    def __str__(self):
        return f"{self.name} ({self.get_isp_type_display()})"


class ISPMetric(models.Model):
    connection = models.ForeignKey(ISPConnection, on_delete=models.CASCADE, related_name='metrics')
    metric_name = models.CharField(max_length=100)  # latency, packet_loss, bandwidth_usage
    value = models.FloatField()
    unit = models.CharField(max_length=20)  # ms, %, Mbps
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['connection', 'metric_name', 'timestamp']),
        ]
        ordering = ["-timestamp"]
    
    def __str__(self):
        return f"{self.connection.name} - {self.metric_name}: {self.value}{self.unit}"


class ISPFailover(models.Model):
    """Track ISP failover events"""
    primary_isp = models.ForeignKey(ISPConnection, on_delete=models.CASCADE, related_name='primary_failovers')
    backup_isp = models.ForeignKey(ISPConnection, on_delete=models.CASCADE, related_name='backup_failovers', null=True, blank=True)
    failover_time = models.DateTimeField()
    recovery_time = models.DateTimeField(null=True, blank=True)
    reason = models.CharField(max_length=200)
    duration_minutes = models.IntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ["-failover_time"]
    
    def __str__(self):
        return f"Failover from {self.primary_isp.name} at {self.failover_time}"


class DeviceBandwidthMeasurement(models.Model):
    """Store bandwidth measurements for network devices"""
    device = models.ForeignKey(NetworkDevice, on_delete=models.CASCADE, related_name='bandwidth_measurements')
    interface = models.CharField(max_length=100, blank=True, null=True, help_text="Network interface name")
    bytes_in = models.BigIntegerField(default=0, help_text="Total bytes received")
    bytes_out = models.BigIntegerField(default=0, help_text="Total bytes sent")
    packets_in = models.BigIntegerField(default=0, help_text="Total packets received")
    packets_out = models.BigIntegerField(default=0, help_text="Total packets sent")
    bps_in = models.FloatField(default=0, help_text="Current bits per second (incoming)")
    bps_out = models.FloatField(default=0, help_text="Current bits per second (outgoing)")
    pps_in = models.FloatField(default=0, help_text="Current packets per second (incoming)")
    pps_out = models.FloatField(default=0, help_text="Current packets per second (outgoing)")
    measurement_method = models.CharField(max_length=20, default='snmp', 
                                       choices=[('snmp', 'SNMP'), ('netstat', 'NetStat'), ('arp', 'ARP')])
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['device', 'timestamp']),
            models.Index(fields=['device', 'interface', 'timestamp']),
        ]
        ordering = ["-timestamp"]
    
    def __str__(self):
        interface_str = f" ({self.interface})" if self.interface else ""
        return f"{self.device.name}{interface_str}: {self.bps_in + self.bps_out:.0f} bps"
    
    @property
    def total_bps(self):
        """Total bandwidth in bits per second"""
        return self.bps_in + self.bps_out
    
    @property
    def total_pps(self):
        """Total packets per second"""
        return self.pps_in + self.pps_out
    
    @property
    def mbps_in(self):
        """Incoming bandwidth in megabits per second"""
        return self.bps_in / 1_000_000
    
    @property
    def mbps_out(self):
        """Outgoing bandwidth in megabits per second"""
        return self.bps_out / 1_000_000
    
    @property
    def total_mbps(self):
        """Total bandwidth in megabits per second"""
        return self.total_bps / 1_000_000


class SSLCertificate(models.Model):
    """Model for SSL/TLS certificate monitoring"""
    server = models.ForeignKey(
        'Server',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ssl_certificates_list',
        help_text="Associated server for this certificate"
    )
    name = models.CharField(max_length=200, help_text="Certificate name or domain")
    domain = models.CharField(max_length=255, help_text="Primary domain")
    alternative_names = models.JSONField(default=list, help_text="SAN domains")
    serial_number = models.CharField(max_length=100, blank=True, null=True)
    key_type = models.CharField(max_length=20, choices=[
        ('RSA', 'RSA'),
        ('ECDSA', 'ECDSA'),
        ('DSA', 'DSA'),
        ('UNKNOWN', 'Unknown')
    ], default='UNKNOWN')
    issuer = models.CharField(max_length=500, blank=True, null=True)
    subject = models.CharField(max_length=500, blank=True, null=True)
    
    # Certificate paths
    cert_path = models.CharField(max_length=500, blank=True, null=True, help_text="Path to certificate file")
    key_path = models.CharField(max_length=500, blank=True, null=True, help_text="Path to private key file")
    
    # Validity dates
    issued_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_valid = models.BooleanField(default=False, help_text="Certificate is currently valid")
    is_self_signed = models.BooleanField(default=False)
    days_until_expiry = models.IntegerField(null=True, blank=True)
    
    # Monitoring
    enabled = models.BooleanField(default=True)
    last_checked = models.DateTimeField(null=True, blank=True)
    check_frequency = models.IntegerField(default=24, help_text="Check frequency in hours")
    
    # Alert thresholds
    warning_days = models.IntegerField(default=30, help_text="Days before expiry to send warning")
    critical_days = models.IntegerField(default=7, help_text="Days before expiry to send critical alert")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "SSL Certificate"
        verbose_name_plural = "SSL Certificates"
        ordering = ['expires_at']
        indexes = [
            models.Index(fields=['enabled', 'expires_at']),
            models.Index(fields=['domain']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.domain})"
    
    def check_certificate(self):
        """Check certificate status and update expiry information"""
        try:
            import ssl
            import socket
            from datetime import datetime, timezone
            
            # Get certificate from file or remote server
            if self.cert_path and self.cert_path.startswith('/etc/letsencrypt/'):
                cert_data = self._read_certificate_file()
            else:
                cert_data = self._get_remote_certificate()
            
            if cert_data:
                self._parse_certificate_data(cert_data)
                self.last_checked = timezone.now()
                self.save()
                return True
            
        except Exception as e:
            print(f"Error checking certificate for {self.domain}: {e}")
            
        return False
    
    def _read_certificate_file(self):
        """Read certificate from local file"""
        try:
            with open(self.cert_path, 'r') as f:
                cert_data = f.read()
            return cert_data
        except Exception as e:
            print(f"Error reading certificate file {self.cert_path}: {e}")
            return None
    
    def _get_remote_certificate(self):
        """Get certificate from remote server"""
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((self.domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=self.domain) as ssock:
                    cert_der = ssock.getpeercert(binary_form=True)
                    cert_pem = ssl.DER_cert_to_PEM_cert(cert_der)
                    return cert_pem
        except Exception as e:
            print(f"Error getting remote certificate for {self.domain}: {e}")
            return None
    
    def _parse_certificate_data(self, cert_data):
        """Parse certificate data and update model fields"""
        try:
            from cryptography import x509
            from cryptography.hazmat.backends import default_backend
            import OpenSSL
            
            # Parse certificate
            cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert_data)
            
            # Update basic info
            self.serial_number = cert.get_serial_number().__str__()
            self.issuer = cert.get_issuer().CN or 'Unknown'
            self.subject = cert.get_subject().CN or 'Unknown'
            
            # Parse dates
            not_before = datetime.strptime(cert.get_notBefore().decode('ascii'), '%Y%m%d%H%M%SZ').replace(tzinfo=timezone.utc)
            not_after = datetime.strptime(cert.get_notAfter().decode('ascii'), '%Y%m%d%H%M%SZ').replace(tzinfo=timezone.utc)
            
            self.issued_at = not_before
            self.expires_at = not_after
            
            # Calculate days until expiry
            now = timezone.now()
            self.days_until_expiry = (not_after - now).days
            self.is_valid = now >= not_before and now < not_after
            
            # Check if self-signed
            self.is_self_signed = cert.get_issuer() == cert.get_subject()
            
            # Get alternative names
            try:
                for i in range(cert.get_extension_count()):
                    ext = cert.get_extension(i)
                    if ext.get_short_name() == b'subjectAltName':
                        san_str = str(ext)
                        domains = [d.split(':')[1] for d in san_str.split(', ') if d.startswith('DNS:')]
                        self.alternative_names = domains
                        break
            except:
                pass
            
        except Exception as e:
            print(f"Error parsing certificate data: {e}")
    
    def get_status_color(self):
        """Get status color for UI display"""
        if not self.is_valid:
            return 'danger'
        elif self.days_until_expiry <= self.critical_days:
            return 'danger'
        elif self.days_until_expiry <= self.warning_days:
            return 'warning'
        else:
            return 'success'
    
    def get_status_text(self):
        """Get human-readable status text"""
        if not self.is_valid:
            return 'Invalid'
        elif self.days_until_expiry <= 0:
            return 'Expired'
        elif self.days_until_expiry <= self.critical_days:
            return f'Expires in {self.days_until_expiry} days (CRITICAL)'
        elif self.days_until_expiry <= self.warning_days:
            return f'Expires in {self.days_until_expiry} days (WARNING)'
        else:
            return f'Valid for {self.days_until_expiry} days'

    @property
    def status_color_name(self):
        """Get status color name for CSS classes"""
        if not self.is_valid or self.days_until_expiry <= self.critical_days:
            return 'critical'
        elif self.days_until_expiry <= self.warning_days:
            return 'warning'
        else:
            return 'good'

    @property
    def percent_remaining(self):
        """Calculate percentage of life remaining (capped at 100)"""
        if self.days_until_expiry <= 0: return 0
        # Assume a standard 90 day cert life for progress bar if issued_at is missing
        total_days = 90
        if self.issued_at and self.expires_at:
            total_days = (self.expires_at - self.issued_at).days
        
        if total_days <= 0: return 0
        percent = (self.days_until_expiry / total_days) * 100
        return min(100, max(0, percent))


class CCTVDevice(models.Model):
    """Model for CCTV camera devices (NVR/DVR locations with multiple cameras)"""
    name = models.CharField(max_length=200, help_text="Device name/location")
    domain = models.CharField(max_length=100, help_text="Device domain or ID")
    port = models.PositiveIntegerField(default=37777, help_text="Connection port")
    username = models.CharField(max_length=100, default="admin", help_text="Login username")
    password = models.CharField(max_length=255, default="admin123456", help_text="Login password (encrypted)")
    protocol = models.CharField(max_length=10, default="1", help_text="Protocol version")
    connect = models.CharField(max_length=10, default="19", help_text="Connection type")
    camera_count = models.PositiveIntegerField(default=4, help_text="Number of cameras at this location")
    is_active = models.BooleanField(default=True, help_text="Device is currently accessible")
    last_checked = models.DateTimeField(null=True, blank=True, help_text="Last time device was checked")
    status = models.CharField(max_length=20, default="unknown", choices=[
        ("online", "Online"),
        ("offline", "Offline"), 
        ("unknown", "Unknown")
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "CCTV Device"
        verbose_name_plural = "CCTV Devices"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.domain})"
    
    def get_camera_list(self):
        """Get list of camera numbers for this device"""
        return list(range(1, self.camera_count + 1))
    
    def get_camera_name(self, camera_number):
        """Get formatted camera name for display"""
        return f"{self.name} - Camera {camera_number}"
    
    def get_rtsp_url(self, camera_number):
        """Generate RTSP URL for specific camera using Dahua format"""
        try:
            from .dahua_http_api import get_dahua_rtsp_url
            return get_dahua_rtsp_url(self.domain, 554, self.username, self.password, camera_number - 1)
        except ImportError:
            # Fallback to basic format
            return f"rtsp://{self.username}:{self.password}@{self.domain}:554/cam/realmonitor?channel={camera_number}&subtype=0"
    
    def check_status(self):
        """Check if device is accessible via Dahua methods"""
        self.last_checked = timezone.now()
        
        try:
            # Log the attempt
            print(f"Checking status for {self.name} at {self.domain}:{self.port}")
            
            # Use the Dahua API integration
            from .dahua_api import check_dahua_device_status
            
            if check_dahua_device_status(self.domain, self.port):
                self.status = "online"
                print(f"{self.name} is ONLINE")
            else:
                self.status = "offline"
                print(f"{self.name} is OFFLINE")
            
        except Exception as e:
            print(f"Unexpected error for {self.name}: {e}")
            self.status = "unknown"
            
        self.save()
