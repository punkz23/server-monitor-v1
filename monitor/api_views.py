from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
import json

from .models import (
    Server, NetworkDevice, NetworkInterface, NetworkMetric,
    SecurityEvent, TrafficLog, ISPConnection, ISPMetric, ISPFailover,
    DeviceBandwidthMeasurement, AlertEvent, CheckResult, ResourceSample,
    DiskIOSample, DiskUsageSample, NetworkSample, RebootEvent, DbSample,
    CCTVDevice, SSLCertificate
)
from .serializers import (
    ServerSerializer, NetworkDeviceSerializer, NetworkInterfaceSerializer,
    NetworkMetricSerializer, SecurityEventSerializer, TrafficLogSerializer,
    ISPConnectionSerializer, ISPMetricSerializer, ISPFailoverSerializer,
    DeviceBandwidthMeasurementSerializer, AlertEventSerializer,
    CheckResultSerializer, ResourceSampleSerializer, DiskIOSampleSerializer,
    DiskUsageSampleSerializer, NetworkSampleSerializer, RebootEventSerializer,
    DbSampleSerializer, CCTVDeviceSerializer, ServerStatusSerializer,
    NetworkDeviceSummarySerializer, SSLCertificateSerializer
)
from .permissions import (
    CanManageServers, CanViewAlerts, CanManageNetworkDevices,
    HasMobileAppPermission, IsAgentUser
)
from .alerts import evaluate_alerts_for_server
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


class ServerViewSet(viewsets.ModelViewSet):
    """
    API endpoint for servers that allows full CRUD operations.
    """
    queryset = Server.objects.all()
    serializer_class = ServerSerializer
    permission_classes = [CanManageServers]
    
    def get_queryset(self):
        queryset = Server.objects.all()
        enabled = self.request.query_params.get('enabled')
        server_type = self.request.query_params.get('server_type')
        
        if enabled is not None:
            queryset = queryset.filter(enabled=enabled.lower() == 'true')
        if server_type:
            queryset = queryset.filter(server_type=server_type)
            
        return queryset.order_by('-pinned', 'name')


class NetworkDeviceViewSet(viewsets.ModelViewSet):
    """
    API endpoint for network devices that allows full CRUD operations.
    """
    queryset = NetworkDevice.objects.all()
    serializer_class = NetworkDeviceSerializer
    permission_classes = [CanManageNetworkDevices]
    
    def get_queryset(self):
        queryset = NetworkDevice.objects.all()
        device_type = self.request.query_params.get('device_type')
        is_active = self.request.query_params.get('is_active')
        
        if device_type:
            queryset = queryset.filter(device_type=device_type)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
            
        return queryset.order_by('-last_seen', 'name')


class AlertEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for alert events (read-only).
    """
    queryset = AlertEvent.objects.all()
    serializer_class = AlertEventSerializer
    permission_classes = [CanViewAlerts]
    
    def get_queryset(self):
        queryset = AlertEvent.objects.select_related('server', 'rule').order_by('-created_at')
        server_id = self.request.query_params.get('server_id')
        severity = self.request.query_params.get('severity')
        
        if server_id:
            queryset = queryset.filter(server_id=server_id)
        if severity:
            queryset = queryset.filter(severity=severity)
            
        return queryset


class ISPConnectionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for ISP connections that allows full CRUD operations.
    """
    queryset = ISPConnection.objects.all()
    serializer_class = ISPConnectionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = ISPConnection.objects.all()
        is_active = self.request.query_params.get('is_active')
        
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
            
        return queryset.order_by('-created_at', 'name')


class CCTVDeviceViewSet(viewsets.ModelViewSet):
    """
    API endpoint for CCTV devices that allows full CRUD operations.
    """
    queryset = CCTVDevice.objects.all()
    serializer_class = CCTVDeviceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = CCTVDevice.objects.all()
        is_active = self.request.query_params.get('is_active')
        
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
            
        return queryset.order_by('-last_checked', 'name')


# Mobile API specific views
@api_view(['GET'])
@permission_classes([HasMobileAppPermission])
def mobile_server_status(request):
    """
    Mobile API: Get server status summary for dashboard
    """
    servers = Server.objects.filter(enabled=True).order_by('-pinned', 'name')
    serializer = ServerStatusSerializer(servers, many=True)
    return Response({
        'servers': serializer.data,
        'timestamp': timezone.now().isoformat()
    })


@api_view(['GET'])
@permission_classes([HasMobileAppPermission])
def mobile_network_devices(request):
    """
    Mobile API: Get network device summary
    """
    devices = NetworkDevice.objects.filter(is_active=True).order_by('-last_seen', 'name')
    serializer = NetworkDeviceSummarySerializer(devices, many=True)
    return Response({
        'devices': serializer.data,
        'timestamp': timezone.now().isoformat()
    })


@api_view(['POST'])
@permission_classes([HasMobileAppPermission])
def mobile_trigger_network_scan(request):
    """
    Mobile API: Trigger a network scan and return updated device list
    """
    from .services.network_scanner import NetworkScanner
    
    scanner = NetworkScanner(timeout=2, max_threads=30)
    networks = scanner.get_local_networks()
    
    # Include the primary network if not detected
    if "192.168.253.0/24" not in networks:
        networks.insert(0, "192.168.253.0/24")
    
    all_discovered = []
    for network in networks:
        try:
            discovered = scanner.scan_network(network)
            all_discovered.extend(discovered)
        except Exception as e:
            print(f"Error scanning {network}: {e}")
            
    # Update database with discovered devices
    for dev_info in all_discovered:
        try:
            NetworkDevice.objects.update_or_create(
                ip_address=dev_info['ip_address'],
                defaults={
                    'name': dev_info.get('hostname') or f"Device-{dev_info['ip_address']}",
                    'mac_address': dev_info.get('mac_address'),
                    'vendor': dev_info.get('vendor', 'Unknown'),
                    'device_type': dev_info.get('device_type', NetworkDevice.TYPE_UNKNOWN),
                    'is_active': True,
                    'last_seen': timezone.now(),
                    'auto_discovered': True
                }
            )
        except Exception as e:
            print(f"Error saving device {dev_info.get('ip_address')}: {e}")

    # Return the full updated list
    devices = NetworkDevice.objects.filter(is_active=True).order_by('-last_seen', 'name')
    serializer = NetworkDeviceSummarySerializer(devices, many=True)
    
    return Response({
        'success': True,
        'devices': serializer.data,
        'count': len(all_discovered),
        'timestamp': timezone.now().isoformat()
    })


@api_view(['GET'])
@permission_classes([HasMobileAppPermission])
def mobile_server_detail(request, server_id):
    """
    Mobile API: Get detailed server information
    """
    server = get_object_or_404(Server, pk=server_id)
    serializer = ServerSerializer(server)
    
    # Get recent resource samples
    recent_resources = ResourceSample.objects.filter(
        server=server
    ).order_by('-collected_at')[:10]
    
    # Get recent check results
    recent_checks = CheckResult.objects.filter(
        server=server
    ).order_by('-checked_at')[:10]
    
    return Response({
        'server': serializer.data,
        'recent_resources': ResourceSampleSerializer(recent_resources, many=True).data,
        'recent_checks': CheckResultSerializer(recent_checks, many=True).data,
        'timestamp': timezone.now().isoformat()
    })


@api_view(['GET'])
@permission_classes([HasMobileAppPermission])
def mobile_alerts(request):
    """
    Mobile API: Get recent alerts
    """
    limit = min(int(request.GET.get('limit', 50)), 200)
    server_id = request.GET.get('server_id')
    severity = request.GET.get('severity')
    
    alerts = AlertEvent.objects.select_related('server', 'rule').order_by('-created_at')
    
    if server_id:
        alerts = alerts.filter(server_id=server_id)
    if severity:
        alerts = alerts.filter(severity=severity)
    
    alerts = alerts[:limit]
    serializer = AlertEventSerializer(alerts, many=True)
    
    return Response({
        'alerts': serializer.data,
        'limit': limit,
        'timestamp': timezone.now().isoformat()
    })


@api_view(['GET'])
@permission_classes([HasMobileAppPermission])
def mobile_metrics_history(request, server_id):
    """
    Mobile API: Get historical metrics for a server
    """
    server = get_object_or_404(Server, pk=server_id)
    
    # Parse range parameter
    range_param = request.GET.get('range', '30')
    max_points = 200
    
    if range_param.endswith('h'):
        try:
            hours = int(range_param[:-1])
            since = timezone.now() - timedelta(hours=hours)
        except ValueError:
            since = timezone.now() - timedelta(hours=30)
    elif range_param.endswith('d'):
        try:
            days = int(range_param[:-1])
            since = timezone.now() - timedelta(days=days)
        except ValueError:
            since = timezone.now() - timedelta(days=7)
    else:
        try:
            limit = int(range_param)
            since = None
        except ValueError:
            limit = 30
            since = None
    
    # Get resource samples
    resource_qs = ResourceSample.objects.filter(server=server).order_by('-collected_at')
    if since:
        resource_qs = resource_qs.filter(collected_at__gte=since)
    resource_samples = resource_qs[:max_points]
    
    # Get network samples
    network_qs = NetworkSample.objects.filter(server=server).order_by('-collected_at')
    if since:
        network_qs = network_qs.filter(collected_at__gte=since)
    network_samples = network_qs[:max_points]
    
    return Response({
        'server': {
            'id': server.id,
            'name': server.name,
            'server_type': server.server_type,
            'ip_address': server.ip_address
        },
        'range': range_param,
        'resource_samples': ResourceSampleSerializer(resource_samples, many=True).data,
        'network_samples': NetworkSampleSerializer(network_samples, many=True).data,
        'timestamp': timezone.now().isoformat()
    })


@api_view(['POST'])
@permission_classes([IsAgentUser])
def mobile_agent_ingest(request):
    """
    Mobile API: Agent data ingestion endpoint
    """
    # This is a simplified version of the original agent_ingest_api
    # In production, you might want to use token authentication instead
    
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return Response({'error': 'invalid_json'}, status=status.HTTP_400_BAD_REQUEST)
    
    # For mobile API, we'll require server_id to be provided
    server_id = payload.get('server_id')
    if not server_id:
        return Response({'error': 'server_id_required'}, status=status.HTTP_400_BAD_REQUEST)
    
    server = get_object_or_404(Server, pk=server_id)
    
    # Process the payload (simplified version)
    collected_at = timezone.now()
    
    # Create resource sample
    cpu = payload.get('cpu', {})
    memory = payload.get('memory', {})
    load = payload.get('load', {})
    
    with transaction.atomic():
        ResourceSample.objects.create(
            server=server,
            collected_at=collected_at,
            cpu_percent=cpu.get('percent'),
            ram_percent=memory.get('percent'),
            load_1=load.get('1'),
            load_5=load.get('5'),
            load_15=load.get('15'),
        )
        
        # Update server status
        server.last_resource_checked = collected_at
        server.last_cpu_percent = cpu.get('percent')
        server.last_ram_percent = memory.get('percent')
        server.last_load_1 = load.get('1')
        server.save(update_fields=[
            'last_resource_checked', 'last_cpu_percent', 
            'last_ram_percent', 'last_load_1'
        ])
    
    # Send WebSocket notification
    channel_layer = get_channel_layer()
    if channel_layer:
        evaluate_alerts_for_server(server=server, now=collected_at, channel_layer=channel_layer)
    
    return Response({
        'ok': True, 
        'server_id': server.id, 
        'collected_at': collected_at.isoformat()
    })


@api_view(['GET'])
@permission_classes([HasMobileAppPermission])
def mobile_dashboard_summary(request):
    """
    Mobile API: Get dashboard summary with counts and status
    """
    # Server counts
    enabled_servers_qs = Server.objects.filter(enabled=True)
    total_servers = enabled_servers_qs.count()
    online_servers = enabled_servers_qs.filter(last_status='UP').count()
    
    # Network device counts
    active_devices = NetworkDevice.objects.filter(is_active=True).count()
    
    # Recent alerts
    recent_alerts_qs = AlertEvent.objects.filter(
        created_at__gte=timezone.now() - timedelta(hours=24)
    ).order_by('-created_at')
    
    recent_alerts_count = recent_alerts_qs.count()
    critical_alerts_count = recent_alerts_qs.filter(severity='CRITICAL', is_recovery=False).count()
    
    # Top 5 most recent alerts for the dashboard
    top_alerts = AlertEventSerializer(recent_alerts_qs[:5], many=True).data
    
    # Status by type for a quick breakdown chart on mobile
    status_by_type = {}
    for s_type, label in Server.TYPE_CHOICES:
        type_qs = enabled_servers_qs.filter(server_type=s_type)
        if type_qs.exists():
            status_by_type[label] = {
                'total': type_qs.count(),
                'online': type_qs.filter(last_status='UP').count()
            }

    return Response({
        'summary': {
            'servers_online': online_servers,
            'servers_total': total_servers,
            'devices_online': active_devices,
            'alerts_24h': recent_alerts_count,
            'critical_alerts': critical_alerts_count,
        },
        'status_by_type': status_by_type,
        'top_alerts': top_alerts,
        'timestamp': timezone.now().isoformat()
    })


class SSLCertificateViewSet(viewsets.ModelViewSet):
    """
    API endpoint for SSL certificates that allows full CRUD operations.
    """
    queryset = SSLCertificate.objects.all()
    serializer_class = SSLCertificateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = SSLCertificate.objects.all()
        enabled = self.request.query_params.get('enabled')
        
        if enabled is not None:
            queryset = queryset.filter(enabled=enabled.lower() == 'true')
        
        return queryset.order_by('expires_at')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def check_certificate(request, pk):
    """Check a specific certificate"""
    certificate = get_object_or_404(SSLCertificate, pk=pk)
    
    from .services.certificate_monitor import CertificateMonitor
    monitor = CertificateMonitor()
    
    result = monitor.check_certificate(certificate)
    
    if result['status'] == 'success':
        return Response({
            'success': True,
            'certificate': SSLCertificateSerializer(certificate).data,
            'message': 'Certificate checked successfully'
        })
    else:
        return Response({
            'success': False,
            'error': result.get('error', 'Unknown error'),
            'message': 'Failed to check certificate'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def check_all_certificates(request):
    """Check all enabled certificates"""
    from .services.certificate_monitor import CertificateMonitor
    monitor = CertificateMonitor()
    
    results = monitor.check_all_certificates()
    
    success_count = len([r for r in results if r['status'] == 'success'])
    total_count = len(results)
    
    return Response({
        'success': True,
        'message': f'Checked {total_count} certificates, {success_count} successful',
        'results': results
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def certificate_status_summary(request):
    """Get certificate status summary"""
    from .services.certificate_monitor import CertificateMonitor
    monitor = CertificateMonitor()
    
    summary = monitor.get_certificate_status_summary()
    
    return Response({
        'success': True,
        'summary': summary
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_certificate_from_info(request):
    """Add certificate from parsed certificate information"""
    from .services.certificate_monitor import CertificateMonitor
    monitor = CertificateMonitor()
    
    cert_info = request.data.get('certificate_info')
    if not cert_info:
        return Response({
            'success': False,
            'error': 'certificate_info is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    certificate = monitor.add_certificate_from_info(cert_info)
    
    if certificate:
        return Response({
            'success': True,
            'certificate': SSLCertificateSerializer(certificate).data,
            'message': 'Certificate added successfully'
        })
    else:
        return Response({
            'success': False,
            'error': 'Failed to add certificate'
        }, status=status.HTTP_400_BAD_REQUEST)
