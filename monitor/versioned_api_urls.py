from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken import views as drf_views

from .api_views import (
    ServerViewSet, NetworkDeviceViewSet, AlertEventViewSet,
    ISPConnectionViewSet, CCTVDeviceViewSet, SSLCertificateViewSet,
    mobile_server_status, mobile_network_devices, mobile_server_detail,
    mobile_alerts, mobile_metrics_history, mobile_agent_ingest,
    mobile_dashboard_summary, check_certificate, check_all_certificates,
    certificate_status_summary, add_certificate_from_info,
    mobile_trigger_network_scan, mobile_add_network_device,
    mobile_clear_network_devices
)
from .auth_views import (
    mobile_login, mobile_logout, mobile_token_info, mobile_refresh_token,
    mobile_register, mobile_profile, mobile_update_profile, mobile_change_password
)
from .v1_urls import urlpatterns as v1_urlpatterns
from .v2_urls import urlpatterns as v2_urlpatterns
from . import api_urls

# API version information
API_VERSIONS = {
    'v1': {
        'status': 'current',
        'deprecated': False,
        'sunset_date': None,
    },
    'v2': {
        'status': 'beta',
        'deprecated': False,
        'sunset_date': None,
    }
}

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'servers', ServerViewSet, basename='server')
router.register(r'network-devices', NetworkDeviceViewSet, basename='networkdevice')
router.register(r'alerts', AlertEventViewSet, basename='alert')
router.register(r'isp-connections', ISPConnectionViewSet, basename='ispconnection')
router.register(r'cctv-devices', CCTVDeviceViewSet, basename='cctvdevice')
router.register(r'certificates', SSLCertificateViewSet, basename='certificate')

# Authentication URLs (non-versioned)
auth_urlpatterns = [
    # Standard DRF token auth
    path('token/', drf_views.obtain_auth_token, name='api-token-auth'),
    
    # Mobile authentication endpoints
    path('login/', mobile_login, name='mobile-login'),
    path('logout/', mobile_logout, name='mobile-logout'),
    path('register/', mobile_register, name='mobile-register'),
    path('token/info/', mobile_token_info, name='mobile-token-info'),
    path('token/refresh/', mobile_refresh_token, name='mobile-token-refresh'),
    path('profile/', mobile_profile, name='mobile-profile'),
    path('profile/update/', mobile_update_profile, name='mobile-update-profile'),
    path('profile/change-password/', mobile_change_password, name='mobile-change-password'),
]

# Version 1 URL patterns
v1_patterns = [
    # V1 specific endpoints
    path('mobile/', include([
        path('dashboard/', mobile_dashboard_summary, name='v1-mobile-dashboard-summary'),
        path('server-status/', mobile_server_status, name='v1-mobile-server-status'),
        path('network-devices/', mobile_network_devices, name='v1-mobile-network-devices'),
        path('network-devices/scan/', mobile_trigger_network_scan, name='v1-mobile-network-scan'),
        path('network-devices/add/', mobile_add_network_device, name='v1-mobile-add-network-device'),
        path('network-devices/clear/', mobile_clear_network_devices, name='v1-mobile-clear-network-devices'),
        path('server/<int:server_id>/', mobile_server_detail, name='v1-mobile-server-detail'),
        path('alerts/', mobile_alerts, name='v1-mobile-alerts'),
        path('server/<int:server_id>/metrics/', mobile_metrics_history, name='v1-mobile-metrics-history'),
        path('agent/ingest/', mobile_agent_ingest, name='v1-mobile-agent-ingest'),
        
        # Certificate endpoints
        path('certificates/summary/', certificate_status_summary, name='v1-certificate-summary'),
        path('certificates/check-all/', check_all_certificates, name='v1-check-all-certificates'),
        path('certificates/add-from-info/', add_certificate_from_info, name='v1-add-certificate-from-info'),
    ])),
    
    # Standard REST endpoints
    path('', include(router.urls)),
    
    # Certificate-specific endpoints
    path('certificates/<int:pk>/check/', check_certificate, name='v1-check-certificate'),
]

# Version 2 URL patterns (future expansion)
v2_patterns = [
    # V2 specific endpoints will be added here
    path('mobile/', include([
        path('dashboard/', mobile_dashboard_summary, name='v2-mobile-dashboard-summary'),
        path('server-status/', mobile_server_status, name='v2-mobile-server-status'),
        path('network-devices/', mobile_network_devices, name='v2-mobile-network-devices'),
        path('network-devices/scan/', mobile_trigger_network_scan, name='v2-mobile-network-scan'),
        path('network-devices/add/', mobile_add_network_device, name='v2-mobile-add-network-device'),
        path('server/<int:server_id>/', mobile_server_detail, name='v2-mobile-server-detail'),
        path('alerts/', mobile_alerts, name='v2-mobile-alerts'),
        path('server/<int:server_id>/metrics/', mobile_metrics_history, name='v2-mobile-metrics-history'),
        path('agent/ingest/', mobile_agent_ingest, name='v2-mobile-agent-ingest'),
        # Add V2 specific endpoints here
        path('server-status/v2/', mobile_server_status, name='v2-mobile-server-status-v2'),
        
        # Certificate endpoints
        path('certificates/summary/', certificate_status_summary, name='v2-certificate-summary'),
        path('certificates/check-all/', check_all_certificates, name='v2-check-all-certificates'),
        path('certificates/add-from-info/', add_certificate_from_info, name='v2-add-certificate-from-info'),
    ])),
    
    # Standard REST endpoints
    path('', include(router.urls)),
    
    # Certificate-specific endpoints
    path('certificates/<int:pk>/check/', check_certificate, name='v2-check-certificate'),
]

# API version URL patterns
versioned_urlpatterns = [
    # Version 1
    path('v1/', include(v1_patterns + v1_urlpatterns)),
    
    # Version 2
    path('v2/', include(v2_patterns + v2_urlpatterns)),
]

# Legacy (non-versioned) API URLs - defaults to v1
legacy_urlpatterns = [
    path('auth/', include(auth_urlpatterns)),
    path('mobile/', include([
        path('dashboard/', mobile_dashboard_summary, name='mobile-dashboard-summary'),
        path('server-status/', mobile_server_status, name='mobile-server-status'),
        path('network-devices/', mobile_network_devices, name='mobile-network-devices'),
        path('network-devices/scan/', mobile_trigger_network_scan, name='mobile-network-scan'),
        path('network-devices/add/', mobile_add_network_device, name='mobile-add-network-device'),
        path('network-devices/clear/', mobile_clear_network_devices, name='mobile-clear-network-devices'),
        path('server/<int:server_id>/', mobile_server_detail, name='mobile-server-detail'),
        path('alerts/', mobile_alerts, name='mobile-alerts'),
        path('server/<int:server_id>/metrics/', mobile_metrics_history, name='mobile-metrics-history'),
        path('agent/ingest/', mobile_agent_ingest, name='mobile-agent-ingest'),
        
        # Certificate endpoints
        path('certificates/summary/', certificate_status_summary, name='certificate-summary'),
        path('certificates/check-all/', check_all_certificates, name='check-all-certificates'),
        path('certificates/add-from-info/', add_certificate_from_info, name='add-certificate-from-info'),
    ])),
    path('', include(router.urls)),
    
    # Certificate-specific endpoints
    path('certificates/<int:pk>/check/', check_certificate, name='check-certificate'),
]

# API information endpoint
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([AllowAny])
def api_info(request):
    """
    API information and version details
    """
    version = getattr(request, 'api_version', '1')
    
    return Response({
        'api_name': 'Django ServerWatch API',
        'version': version,
        'supported_versions': list(API_VERSIONS.keys()),
        'default_version': '1',
        'versioning_strategies': {
            'url_path': '/api/v1/, /api/v2/',
            'header': 'Accept: application/vnd.api+json;version=1',
            'query_param': '?version=1',
            'custom_header': 'X-API-Version: 1'
        },
        'versions': API_VERSIONS,
        'endpoints': {
            'authentication': '/api/auth/',
            'mobile': '/api/mobile/',
            'servers': '/api/servers/',
            'network_devices': '/api/network-devices/',
            'alerts': '/api/alerts/',
        },
        'documentation': {
            'v1': '/api/v1/docs/',
            'v2': '/api/v2/docs/',
        }
    })

# Combine all API URLs
urlpatterns = [
    # API information
    path('info/', api_info, name='api-info'),
    
    # Authentication endpoints (non-versioned)
    path('auth/', include(auth_urlpatterns)),
    
    # DTR Biometric Monitoring endpoints (non-versioned)
    path('dtr/', include(api_urls.dtr_urlpatterns)),
    
    # Versioned endpoints
    path('', include(versioned_urlpatterns)),
    
    # Legacy endpoints (defaults to v1)
    path('', include(legacy_urlpatterns)),
]
