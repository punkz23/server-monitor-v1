from rest_framework import serializers
from .models import (
    Server, NetworkDevice, NetworkInterface, NetworkMetric,
    SecurityEvent, TrafficLog, ISPConnection, ISPMetric, ISPFailover,
    DeviceBandwidthMeasurement, AlertEvent, CheckResult, ResourceSample,
    DiskIOSample, DiskUsageSample, NetworkSample, RebootEvent, DbSample,
    CCTVDevice, SSLCertificate
)


class ServerSerializer(serializers.ModelSerializer):
    server_type_display = serializers.CharField(source='get_server_type_display', read_only=True)
    last_status_display = serializers.CharField(source='get_last_status_display', read_only=True)
    
    class Meta:
        model = Server
        fields = '__all__'


class NetworkDeviceSerializer(serializers.ModelSerializer):
    device_type_display = serializers.CharField(source='get_device_type_display', read_only=True)
    
    class Meta:
        model = NetworkDevice
        fields = '__all__'


class NetworkInterfaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkInterface
        fields = '__all__'


class NetworkMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkMetric
        fields = '__all__'


class SecurityEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecurityEvent
        fields = '__all__'


class TrafficLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficLog
        fields = '__all__'


class ISPConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ISPConnection
        fields = '__all__'


class ISPMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = ISPMetric
        fields = '__all__'


class ISPFailoverSerializer(serializers.ModelSerializer):
    class Meta:
        model = ISPFailover
        fields = '__all__'


class DeviceBandwidthMeasurementSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceBandwidthMeasurement
        fields = '__all__'


class AlertEventSerializer(serializers.ModelSerializer):
    server_name = serializers.CharField(source='server.name', read_only=True)
    
    class Meta:
        model = AlertEvent
        fields = '__all__'


class CheckResultSerializer(serializers.ModelSerializer):
    server_name = serializers.CharField(source='server.name', read_only=True)
    
    class Meta:
        model = CheckResult
        fields = '__all__'


class ResourceSampleSerializer(serializers.ModelSerializer):
    server_name = serializers.CharField(source='server.name', read_only=True)
    
    class Meta:
        model = ResourceSample
        fields = '__all__'


class DiskIOSampleSerializer(serializers.ModelSerializer):
    server_name = serializers.CharField(source='server.name', read_only=True)
    
    class Meta:
        model = DiskIOSample
        fields = '__all__'


class DiskUsageSampleSerializer(serializers.ModelSerializer):
    server_name = serializers.CharField(source='server.name', read_only=True)
    
    class Meta:
        model = DiskUsageSample
        fields = '__all__'


class NetworkSampleSerializer(serializers.ModelSerializer):
    server_name = serializers.CharField(source='server.name', read_only=True)
    
    class Meta:
        model = NetworkSample
        fields = '__all__'


class RebootEventSerializer(serializers.ModelSerializer):
    server_name = serializers.CharField(source='server.name', read_only=True)
    
    class Meta:
        model = RebootEvent
        fields = '__all__'


class DbSampleSerializer(serializers.ModelSerializer):
    server_name = serializers.CharField(source='server.name', read_only=True)
    
    class Meta:
        model = DbSample
        fields = '__all__'


class CCTVDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CCTVDevice
        fields = '__all__'


# Summary serializers for mobile API
class ServerStatusSerializer(serializers.ModelSerializer):
    server_type_display = serializers.CharField(source='get_server_type_display', read_only=True)
    last_status_display = serializers.CharField(source='get_last_status_display', read_only=True)
    
    class Meta:
        model = Server
        fields = [
            'id', 'name', 'pinned', 'tags', 'server_type', 'server_type_display',
            'ip_address', 'port', 'last_status', 'last_status_display',
            'last_http_ok', 'last_latency_ms', 'last_http_status_code',
            'last_checked', 'last_error', 'last_resource_checked',
            'last_cpu_percent', 'last_ram_percent', 'last_load_1',
            'last_uptime_seconds', 'last_boot_time'
        ]


class NetworkDeviceSummarySerializer(serializers.ModelSerializer):
    device_type_display = serializers.CharField(source='get_device_type_display', read_only=True)
    
    class Meta:
        model = NetworkDevice
        fields = [
            'id', 'name', 'device_type', 'device_type_display', 'ip_address',
            'mac_address', 'vendor', 'hostname', 'is_active', 'last_seen'
        ]


class SSLCertificateSerializer(serializers.ModelSerializer):
    status_color = serializers.CharField(read_only=True)
    status_text = serializers.CharField(read_only=True)
    
    class Meta:
        model = SSLCertificate
        fields = '__all__'
