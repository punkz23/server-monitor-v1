from django.contrib import admin

from .models import CheckResult, Server, NetworkDevice, NetworkInterface, NetworkMetric, SecurityEvent, TrafficLog, ISPConnection, ISPMetric, ISPFailover, SSLCertificate


@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "server_type",
        "ip_address",
        "port",
        "use_https",
        "http_check",
        "enabled",
        "last_status",
        "last_checked",
        "last_latency_ms",
        "last_http_status_code",
    )
    list_filter = ("enabled", "use_https", "http_check", "last_status")
    search_fields = ("name", "ip_address")


@admin.register(CheckResult)
class CheckResultAdmin(admin.ModelAdmin):
    list_display = (
        "server",
        "checked_at",
        "status",
        "latency_ms",
        "http_status_code",
    )
    list_filter = ("status", "server")
    search_fields = ("server__name", "server__ip_address")


@admin.register(NetworkDevice)
class NetworkDeviceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "device_type",
        "ip_address",
        "mac_address",
        "vendor",
        "hostname",
        "is_active",
        "auto_discovered",
        "last_seen",
    )
    list_filter = ("device_type", "is_active", "auto_discovered", "vendor")
    search_fields = ("name", "ip_address", "mac_address", "hostname", "vendor")
    readonly_fields = ("created_at", "first_seen", "last_seen")
    fieldsets = (
        ("Basic Information", {
            "fields": ("name", "device_type", "ip_address", "mac_address", "vendor", "hostname")
        }),
        ("Discovery", {
            "fields": ("auto_discovered", "is_active", "first_seen", "last_seen")
        }),
        ("Network Details", {
            "fields": ("os_fingerprint", "open_ports")
        }),
        ("SNMP Configuration", {
            "fields": ("snmp_community", "snmp_port")
        }),
        ("API Configuration", {
            "fields": ("api_token", "api_username", "api_port")
        }),
        ("Status", {
            "fields": ("enabled", "notes")
        }),
        ("Timestamps", {
            "fields": ("created_at", "last_checked")
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(NetworkInterface)
class NetworkInterfaceAdmin(admin.ModelAdmin):
    list_display = (
        "device",
        "name",
        "status",
        "speed",
        "mtu",
    )
    list_filter = ("status", "device")
    search_fields = ("device__name", "name")


@admin.register(NetworkMetric)
class NetworkMetricAdmin(admin.ModelAdmin):
    list_display = (
        "device",
        "metric_name",
        "value",
        "unit",
        "timestamp",
    )
    list_filter = ("metric_name", "device", "timestamp")
    search_fields = ("device__name", "metric_name")
    readonly_fields = ("timestamp",)


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    list_display = (
        "device",
        "event_type",
        "action",
        "severity",
        "source_ip",
        "dest_ip",
        "timestamp",
    )
    list_filter = ("event_type", "action", "severity", "device")
    search_fields = ("device__name", "source_ip", "dest_ip", "rule_name")
    readonly_fields = ("timestamp",)


@admin.register(TrafficLog)
class TrafficLogAdmin(admin.ModelAdmin):
    list_display = (
        "interface",
        "bytes_in",
        "bytes_out",
        "packets_in",
        "packets_out",
        "timestamp",
    )
    list_filter = ("interface__device", "timestamp")
    search_fields = ("interface__device__name", "interface__name")
    readonly_fields = ("timestamp",)


@admin.register(ISPConnection)
class ISPConnectionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "isp_type",
        "gateway_ip",
        "bandwidth_mbps",
        "primary_connection",
        "enabled",
        "last_checked",
    )
    list_filter = ("isp_type", "primary_connection", "enabled")
    search_fields = ("name", "gateway_ip")
    readonly_fields = ("created_at",)


@admin.register(ISPMetric)
class ISPMetricAdmin(admin.ModelAdmin):
    list_display = (
        "connection",
        "metric_name",
        "value",
        "unit",
        "timestamp",
    )
    list_filter = ("metric_name", "connection", "timestamp")
    search_fields = ("connection__name", "metric_name")
    readonly_fields = ("timestamp",)


@admin.register(ISPFailover)
class ISPFailoverAdmin(admin.ModelAdmin):
    list_display = (
        "primary_isp",
        "backup_isp",
        "failover_time",
        "recovery_time",
        "duration_minutes",
        "reason",
    )
    list_filter = ("primary_isp", "failover_time")
    search_fields = ("primary_isp__name", "backup_isp__name", "reason")
    readonly_fields = ("failover_time",)


@admin.register(SSLCertificate)
class SSLCertificateAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "domain",
        "key_type",
        "is_valid",
        "days_until_expiry",
        "expires_at",
        "enabled",
        "last_checked",
    )
    list_filter = ("key_type", "is_valid", "enabled", "expires_at")
    search_fields = ("name", "domain", "alternative_names")
    readonly_fields = ("serial_number", "issued_at", "created_at", "updated_at")
    fieldsets = (
        ("Basic Information", {
            "fields": ("name", "domain", "alternative_names", "enabled")
        }),
        ("Certificate Details", {
            "fields": ("serial_number", "key_type", "issuer", "subject")
        }),
        ("File Paths", {
            "fields": ("cert_path", "key_path")
        }),
        ("Validity", {
            "fields": ("issued_at", "expires_at", "is_valid", "is_self_signed")
        }),
        ("Monitoring", {
            "fields": ("days_until_expiry", "last_checked", "check_frequency")
        }),
        ("Alert Thresholds", {
            "fields": ("warning_days", "critical_days")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at")
        }),
    )
    
    actions = ['check_certificates']
    
    def check_certificates(self, request, queryset):
        """Check selected certificates"""
        from .services.certificate_monitor import CertificateMonitor
        monitor = CertificateMonitor()
        checked = 0
        
        for cert in queryset:
            if monitor.check_certificate(cert):
                checked += 1
        
        self.message_user(request, f"Checked {checked} certificates successfully")
    
    check_certificates.short_description = "Check selected certificates"
