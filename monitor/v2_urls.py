from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone

from .api_views import (
    mobile_server_status, mobile_network_devices, mobile_server_detail,
    mobile_alerts, mobile_metrics_history, mobile_agent_ingest,
    mobile_dashboard_summary
)
from .v2_views import (
    v2_mobile_server_status, v2_mobile_dashboard_summary,
    v2_mobile_alerts, v2_server_detail
)
from . import views


@api_view(['GET'])
@permission_classes([AllowAny])
def v2_api_info(request):
    """
    V2 API information endpoint
    """
    return Response({
        'api_name': 'Django ServerWatch API',
        'version': '2',
        'status': 'beta',
        'deprecated': False,
        'endpoints': {
            'mobile': {
                'dashboard': '/api/v2/mobile/dashboard/',
                'server_status': '/api/v2/mobile/server-status/',
                'network_devices': '/api/v2/mobile/network-devices/',
                'server_detail': '/api/v2/mobile/server/{id}/',
                'alerts': '/api/v2/mobile/alerts/',
                'metrics': '/api/v2/mobile/server/{id}/metrics/',
                'agent_ingest': '/api/v2/mobile/agent/ingest/',
                'server_status_v2': '/api/v2/mobile/server-status/v2/',  # V2 enhanced endpoint
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
                'health_score': 'integer',  # V2 addition
                'uptime_percentage': 'float',  # V2 addition
                'response_time_ms': 'integer',  # V2 addition
            }
        },
        'new_features': [
            'Enhanced server health scoring',
            'Improved error handling',
            'Better pagination',
            'Real-time WebSocket support',
            'Enhanced filtering and sorting',
            'Bulk operations support',
        ],
        'breaking_changes': [
            'Server status response format updated',
            'Alert structure enhanced',
            'Metrics data format improved',
        ],
        'version_info': {
            'released': '2026-01-02',
            'deprecated': False,
            'sunset_date': None,
            'migration_guide': '/api/v2/docs/migration-from-v1',
        }
    })


# V2 Mobile API endpoints (enhanced versions)
v2_mobile_urlpatterns = [
    # Enhanced V2 endpoints
    path('dashboard/', v2_mobile_dashboard_summary, name='v2-mobile-dashboard'),
    path('server-status/', v2_mobile_server_status, name='v2-mobile-server-status'),
    path('server-status/v2/', v2_mobile_server_status, name='v2-mobile-server-status-v2'),
    path('network-devices/', mobile_network_devices, name='v2-mobile-network-devices'),
    path('server/<int:server_id>/', v2_server_detail, name='v2-mobile-server-detail'),
    path('alerts/', v2_mobile_alerts, name='v2-mobile-alerts'),
    path('server/<int:server_id>/metrics/', mobile_metrics_history, name='v2-mobile-metrics-history'),
    path('agent/ingest/', mobile_agent_ingest, name='v2-mobile-agent-ingest'),
]

# V2 Metrics API endpoints
v2_metrics_urlpatterns = [
    path('metrics/server/<int:server_id>/detailed/', views.server_detailed_metrics_api, name='v2-server-detailed-metrics-api'),
    path('servers/<int:server_id>/directories/', views.update_server_directories, name='v2-update-server-directories'),
]

# V2 API info
v2_info_urlpatterns = [
    path('info/', v2_api_info, name='v2-api-info'),
]

# Combine all V2 URL patterns
urlpatterns = v2_mobile_urlpatterns + v2_metrics_urlpatterns + v2_info_urlpatterns
