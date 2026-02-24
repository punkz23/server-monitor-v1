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

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'servers', ServerViewSet, basename='server')
router.register(r'network-devices', NetworkDeviceViewSet, basename='networkdevice')
router.register(r'alerts', AlertEventViewSet, basename='alert')
router.register(r'isp-connections', ISPConnectionViewSet, basename='ispconnection')
router.register(r'cctv-devices', CCTVDeviceViewSet, basename='cctvdevice')
router.register(r'certificates', SSLCertificateViewSet, basename='certificate')

# Mobile API URLs
mobile_urlpatterns = [
    # Mobile-specific endpoints
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
]

# Authentication URLs
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

# Combine all API URLs
urlpatterns = [
    path('auth/', include(auth_urlpatterns)),
    path('mobile/', include(mobile_urlpatterns)),
    path('', include(router.urls)),
    
    # Certificate-specific endpoints
    path('certificates/<int:pk>/check/', check_certificate, name='check-certificate'),
]
