from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone

from .api_views import (
    mobile_server_status, mobile_network_devices, mobile_server_detail,
    mobile_alerts, mobile_metrics_history, mobile_agent_ingest,
    mobile_dashboard_summary, mobile_trigger_network_scan
)


@api_view(['GET'])
@permission_classes([AllowAny])
def v1_api_info(request):
    """
    V1 API information endpoint
    """
    return Response({
        'api_name': 'Django ServerWatch API',
        'version': '1',
        'status': 'current',
        'deprecated': False,
        'endpoints': {
            'mobile': {
                'dashboard': '/api/v1/mobile/dashboard/',
                'server_status': '/api/v1/mobile/server-status/',
                'network_devices': '/api/v1/mobile/network-devices/',
                'network_scan': '/api/v1/mobile/network-devices/scan/',
                'server_detail': '/api/v1/mobile/server/{id}/',
                'alerts': '/api/v1/mobile/alerts/',
                'metrics': '/api/v1/mobile/server/{id}/metrics/',
                'agent_ingest': '/api/v1/mobile/agent/ingest/',
            },
            'authentication': {
                'login': '/api/auth/login/',
                'register': '/api/auth/register/',
                'logout': '/api/auth/logout/',
                'token_info': '/api/auth/token/info/',
                'token_refresh': '/api/auth/token/refresh/',
                'profile': '/api/auth/profile/',
            }
        },
        'data_formats': {
            'server_status': {
                'id': 'integer',
                'name': 'string',
                'server_type': 'string',
                'last_status': 'string',
                'last_cpu_percent': 'float',
                'last_ram_percent': 'float',
                'last_checked': 'datetime',
            }
        },
        'version_info': {
            'released': '2026-01-02',
            'deprecated': False,
            'sunset_date': None,
            'migration_guide': '/api/v2/docs/migration-from-v1',
        }
    })


# V1 Mobile API endpoints
v1_mobile_urlpatterns = [
    path('dashboard/', mobile_dashboard_summary, name='v1-mobile-dashboard'),
    path('server-status/', mobile_server_status, name='v1-mobile-server-status'),
    path('network-devices/', mobile_network_devices, name='v1-mobile-network-devices'),
    path('network-devices/scan/', mobile_trigger_network_scan, name='v1-mobile-network-scan'),
    path('server/<int:server_id>/', mobile_server_detail, name='v1-mobile-server-detail'),
    path('alerts/', mobile_alerts, name='v1-mobile-alerts'),
    path('server/<int:server_id>/metrics/', mobile_metrics_history, name='v1-mobile-metrics-history'),
    path('agent/ingest/', mobile_agent_ingest, name='v1-mobile-agent-ingest'),
]

# V1 API info
v1_info_urlpatterns = [
    path('info/', v1_api_info, name='v1-api-info'),
]

# Combine all V1 URL patterns
urlpatterns = v1_mobile_urlpatterns + v1_info_urlpatterns
