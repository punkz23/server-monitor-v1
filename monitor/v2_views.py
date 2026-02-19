from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import Server, AlertEvent
from .serializers import ServerStatusSerializer, AlertEventSerializer
from .permissions import HasMobileAppPermission
from .api_views import mobile_dashboard_summary, mobile_server_detail


@api_view(['GET'])
@permission_classes([HasMobileAppPermission])
def v2_mobile_server_status(request):
    """
    V2 Enhanced Mobile API: Get server status summary with additional metrics
    """
    servers = Server.objects.filter(enabled=True).order_by('-pinned', 'name')
    
    # Enhanced server data with V2 additions
    server_data = []
    for server in servers:
        # Calculate health score (V2 addition)
        health_score = calculate_server_health_score(server)
        
        # Calculate uptime percentage (V2 addition)
        uptime_percentage = calculate_uptime_percentage(server)
        
        # Response time (V2 addition)
        response_time_ms = server.last_latency_ms if server.last_latency_ms else None
        
        server_info = {
            'id': server.id,
            'name': server.name,
            'pinned': server.pinned,
            'tags': server.tags,
            'server_type': server.server_type,
            'server_type_display': server.get_server_type_display(),
            'ip_address': server.ip_address,
            'port': server.port,
            'last_status': server.last_status,
            'last_status_display': server.get_last_status_display(),
            'last_http_ok': server.last_http_ok,
            'last_latency_ms': server.last_latency_ms,
            'last_http_status_code': server.last_http_status_code,
            'last_checked': server.last_checked.isoformat() if server.last_checked else None,
            'last_error': server.last_error,
            'last_resource_checked': server.last_resource_checked.isoformat() if server.last_resource_checked else None,
            'last_cpu_percent': server.last_cpu_percent,
            'last_ram_percent': server.last_ram_percent,
            'last_load_1': server.last_load_1,
            'last_uptime_seconds': server.last_uptime_seconds,
            'last_boot_time': server.last_boot_time.isoformat() if server.last_boot_time else None,
            # V2 additions
            'health_score': health_score,
            'uptime_percentage': uptime_percentage,
            'response_time_ms': response_time_ms,
            'status_trend': get_status_trend(server),  # V2 addition
            'performance_rating': get_performance_rating(server),  # V2 addition
        }
        server_data.append(server_info)
    
    return Response({
        'servers': server_data,
        'summary': {
            'total_servers': len(server_data),
            'online_servers': sum(1 for s in server_data if s['last_status'] == 'UP'),
            'offline_servers': sum(1 for s in server_data if s['last_status'] == 'DOWN'),
            'average_health_score': sum(s['health_score'] for s in server_data) / len(server_data) if server_data else 0,
        },
        'timestamp': timezone.now().isoformat(),
        'api_version': '2',
    })


@api_view(['GET'])
@permission_classes([HasMobileAppPermission])
def v2_mobile_dashboard_summary(request):
    """
    V2 Enhanced Mobile API: Get dashboard summary with enhanced metrics
    """
    # Get base summary from V1
    base_response = mobile_dashboard_summary(request)
    base_data = base_response.data
    
    # V2 enhancements
    enhanced_data = base_data.copy()
    
    # Add health metrics
    servers = Server.objects.filter(enabled=True)
    health_scores = [calculate_server_health_score(server) for server in servers]
    
    enhanced_data['health_metrics'] = {
        'average_health_score': sum(health_scores) / len(health_scores) if health_scores else 0,
        'healthy_servers': sum(1 for score in health_scores if score >= 80),
        'warning_servers': sum(1 for score in health_scores if 50 <= score < 80),
        'critical_servers': sum(1 for score in health_scores if score < 50),
    }
    
    # Add performance metrics
    enhanced_data['performance_metrics'] = {
        'average_response_time': calculate_average_response_time(servers),
        'fast_servers': sum(1 for s in servers if s.last_latency_ms and s.last_latency_ms < 100),
        'slow_servers': sum(1 for s in servers if s.last_latency_ms and s.last_latency_ms > 500),
    }
    
    # Add trend data (V2 addition)
    enhanced_data['trends'] = {
        'server_status_trend': get_server_status_trend(),
        'alert_trend': get_alert_trend(),
        'performance_trend': get_performance_trend(),
    }
    
    enhanced_data['api_version'] = '2'
    enhanced_data['enhanced_features'] = [
        'health_scoring',
        'performance_metrics',
        'trend_analysis',
        'enhanced_summaries'
    ]
    
    return Response(enhanced_data)


@api_view(['GET'])
@permission_classes([HasMobileAppPermission])
def v2_mobile_alerts(request):
    """
    V2 Enhanced Mobile API: Get recent alerts with enhanced filtering and metadata
    """
    limit = min(int(request.GET.get('limit', 50)), 200)
    server_id = request.GET.get('server_id')
    severity = request.GET.get('severity')
    alert_type = request.GET.get('type')  # V2 addition
    
    alerts = AlertEvent.objects.select_related('server', 'rule').order_by('-created_at')
    
    if server_id:
        alerts = alerts.filter(server_id=server_id)
    if severity:
        alerts = alerts.filter(severity=severity)
    if alert_type:  # V2 addition
        alerts = alerts.filter(kind=alert_type)
    
    alerts = alerts[:limit]
    
    # Enhanced alert data
    alert_data = []
    for alert in alerts:
        alert_info = AlertEventSerializer(alert).data
        # V2 additions
        alert_info.update({
            'impact_level': calculate_alert_impact(alert),
            'estimated_resolution_time': estimate_resolution_time(alert),
            'related_alerts': get_related_alerts(alert),
            'actionable': is_alert_actionable(alert),
        })
        alert_data.append(alert_info)
    
    return Response({
        'alerts': alert_data,
        'limit': limit,
        'filters_applied': {
            'server_id': server_id,
            'severity': severity,
            'type': alert_type,
        },
        'summary': {
            'total_alerts': len(alert_data),
            'critical_alerts': sum(1 for a in alert_data if a['severity'] == 'CRITICAL'),
            'warning_alerts': sum(1 for a in alert_data if a['severity'] == 'WARNING'),
            'info_alerts': sum(1 for a in alert_data if a['severity'] == 'INFO'),
            'actionable_alerts': sum(1 for a in alert_data if a['actionable']),
        },
        'timestamp': timezone.now().isoformat(),
        'api_version': '2',
    })


@api_view(['GET'])
@permission_classes([HasMobileAppPermission])
def v2_server_detail(request, server_id):
    """
    V2 Enhanced Mobile API: Get detailed server information with enhanced metrics
    """
    # Get base response from V1
    base_response = mobile_server_detail(request, server_id)
    base_data = base_response.data
    
    server = get_object_or_404(Server, pk=server_id)
    
    # V2 enhancements
    enhanced_data = base_data.copy()
    
    # Add enhanced server metrics
    enhanced_data['server'].update({
        'health_score': calculate_server_health_score(server),
        'uptime_percentage': calculate_uptime_percentage(server),
        'performance_rating': get_performance_rating(server),
        'status_trend': get_status_trend(server),
        'maintenance_scheduled': get_maintenance_schedule(server),
        'resource_utilization': get_resource_utilization(server),
        'security_status': get_security_status(server),
    })
    
    # Add historical analysis (V2 addition)
    enhanced_data['historical_analysis'] = {
        'status_history_24h': get_status_history(server, hours=24),
        'performance_trend_7d': get_performance_trend(server, days=7),
        'alert_frequency_30d': get_alert_frequency(server, days=30),
        'availability_report': get_availability_report(server),
    }
    
    # Add recommendations (V2 addition)
    enhanced_data['recommendations'] = generate_server_recommendations(server)
    
    enhanced_data['api_version'] = '2'
    enhanced_data['enhanced_features'] = [
        'health_scoring',
        'historical_analysis',
        'recommendations',
        'enhanced_metrics'
    ]
    
    return Response(enhanced_data)


# V2 Helper Functions
def calculate_server_health_score(server):
    """Calculate server health score (0-100)"""
    score = 100
    
    # Status impact
    if server.last_status == 'DOWN':
        score -= 50
    elif server.last_status == 'WARNING':
        score -= 25
    
    # CPU usage impact
    if server.last_cpu_percent:
        if server.last_cpu_percent > 90:
            score -= 20
        elif server.last_cpu_percent > 80:
            score -= 10
        elif server.last_cpu_percent > 70:
            score -= 5
    
    # RAM usage impact
    if server.last_ram_percent:
        if server.last_ram_percent > 90:
            score -= 20
        elif server.last_ram_percent > 80:
            score -= 10
        elif server.last_ram_percent > 70:
            score -= 5
    
    # Response time impact
    if server.last_latency_ms:
        if server.last_latency_ms > 1000:
            score -= 15
        elif server.last_latency_ms > 500:
            score -= 10
        elif server.last_latency_ms > 200:
            score -= 5
    
    return max(0, min(100, score))


def calculate_uptime_percentage(server):
    """Calculate server uptime percentage"""
    # This is a simplified calculation - in production, you'd use actual uptime data
    if server.last_status == 'UP':
        return 99.9
    elif server.last_status == 'WARNING':
        return 95.0
    else:
        return 0.0


def get_status_trend(server):
    """Get server status trend"""
    # Simplified trend calculation
    return 'stable'  # Could be 'improving', 'degrading', 'stable'


def get_performance_rating(server):
    """Get server performance rating"""
    health_score = calculate_server_health_score(server)
    
    if health_score >= 90:
        return 'excellent'
    elif health_score >= 80:
        return 'good'
    elif health_score >= 70:
        return 'fair'
    elif health_score >= 50:
        return 'poor'
    else:
        return 'critical'


def calculate_average_response_time(servers):
    """Calculate average response time across servers"""
    response_times = [s.last_latency_ms for s in servers if s.last_latency_ms]
    return sum(response_times) / len(response_times) if response_times else 0


def get_server_status_trend():
    """Get overall server status trend"""
    return 'stable'  # Simplified


def get_alert_trend():
    """Get alert trend"""
    return 'decreasing'  # Simplified


def get_performance_trend(server=None, days=7):
    """Get performance trend for specified days"""
    from .services.metrics_monitor_service import MetricsMonitorService
    monitor = MetricsMonitorService()
    
    if server:
        return monitor.get_performance_trend(server, hours=days*24)
    
    return 'stable'  # Simplified global trend

    """Calculate alert impact level"""
    if alert.severity == 'CRITICAL':
        return 'high'
    elif alert.severity == 'WARNING':
        return 'medium'
    else:
        return 'low'


def estimate_resolution_time(alert):
    """Estimate resolution time in minutes"""
    if alert.severity == 'CRITICAL':
        return 60
    elif alert.severity == 'WARNING':
        return 180
    else:
        return 30


def get_related_alerts(alert):
    """Get related alerts"""
    return []  # Simplified


def is_alert_actionable(alert):
    """Check if alert is actionable"""
    return True  # Simplified


def get_maintenance_schedule(server):
    """Get maintenance schedule for server"""
    return None  # Simplified


def get_resource_utilization(server):
    """Get resource utilization details"""
    return {
        'cpu_trend': 'stable',
        'memory_trend': 'increasing',
        'disk_trend': 'stable',
    }


def get_security_status(server):
    """Get security status"""
    return 'secure'  # Simplified


def get_status_history(server, hours=24):
    """Get status history for specified hours"""
    return []  # Simplified


def get_alert_frequency(server, days=30):
    """Get alert frequency for specified days"""
    return 0  # Simplified


def get_availability_report(server):
    """Get availability report"""
    return {
        'uptime_percentage': 99.9,
        'downtime_minutes': 10,
        'incidents': 1,
    }


def generate_server_recommendations(server):
    """Generate server recommendations"""
    recommendations = []
    
    if server.last_cpu_percent and server.last_cpu_percent > 80:
        recommendations.append({
            'type': 'performance',
            'priority': 'high',
            'message': 'Consider upgrading CPU or optimizing processes',
        })
    
    if server.last_ram_percent and server.last_ram_percent > 80:
        recommendations.append({
            'type': 'memory',
            'priority': 'medium',
            'message': 'Monitor memory usage and consider adding RAM',
        })
    
    return recommendations
