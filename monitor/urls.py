from django.urls import path, include
from . import views
from . import api_views_metrics
from . import views_ssh_credentials
from . import agent_views
from . import agent_deployment_views
from . import versioned_api_urls
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(template_name='monitor/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    path("", views.dashboard, name="dashboard"),
    path("monitoring/", views.monitoring_mode, name="monitoring_mode"),
    path("network/", views.network_dashboard, name="network_dashboard"),
    path("network/devices/", views.network_devices, name="network_devices"),
    path("network/devices/<int:device_id>/", views.device_detail, name="device_detail"),
    path("network/isp/add/", views.isp_add, name="isp_add"),
    path("network/isp/<int:isp_id>/edit/", views.isp_edit, name="isp_edit"),
    path("network/isp/<int:isp_id>/delete/", views.isp_delete, name="isp_delete"),
    path("network/isp/<int:isp_id>/", views.isp_detail, name="isp_detail"),
    path("network/isp/api/status/", views.isp_status_api, name="isp_status_api"),
    path("network/isp/<int:isp_id>/api/metrics/", views.isp_metrics_api, name="isp_metrics_api"),
    path("servers/add/", views.server_add, name="server_add"),
    path("servers/<int:server_id>/edit/", views.server_edit, name="server_edit"),
    path("servers/<int:server_id>/delete/", views.server_delete, name="server_delete"),
    path("servers/<int:server_id>/", views.server_detail, name="server_detail"),
    path("api/status/", views.status_api, name="status_api"),
    path("api/history/", views.history_api, name="history_api"),
    path("api/events/", views.events_api, name="events_api"),
    path("api/resources/history/", views.resource_history_api, name="resource_history_api"),
    path("api/servers/<int:server_id>/series/", views.server_series_api, name="server_series_api"),
    path("api/agent/ingest/", views.agent_ingest_api, name="agent_ingest_api"),
    path(
        "api/servers/<int:server_id>/resources/series/",
        views.resource_series_api,
        name="resource_series_api",
    ),
    path(
        "api/servers/<int:server_id>/resources/disk-usage/",
        views.disk_usage_series_api,
        name="disk_usage_series_api",
    ),
    path(
        "api/servers/<int:server_id>/resources/disk-io/",
        views.disk_io_series_api,
        name="disk_io_series_api",
    ),
    path(
        "api/servers/<int:server_id>/resources/network/",
        views.network_series_api,
        name="network_series_api",
    ),
    path(
        "api/servers/<int:server_id>/db/series/",
        views.db_series_api,
        name="db_series_api",
    ),
    path(
        "api/servers/<int:server_id>/resources/reboots/",
        views.reboot_history_api,
        name="reboot_history_api",
    ),
    # Network Device Discovery APIs
    path('api/network/devices/', views.network_devices_api, name='network_devices_api'),
    path('api/network/scan/', views.scan_network_api, name='scan_network_api'),
    path('api/network/scan/status/', views.network_scan_status_api, name='network_scan_status_api'),
    path('api/network/device/<int:device_id>/', views.network_device_api, name='network_device_api'),
    path('api/network/device/<int:device_id>/update-type/', views.update_device_type_api, name='update_device_type_api'),
    path('api/network/device/<int:device_id>/interfaces/', views.firewall_interfaces_api, name='firewall_interfaces_api'),
    path('api/network/current-connection/', views.current_connection_api, name='current_connection_api'),
    path('network/reports/', views.network_device_reports, name='network_device_reports'),
    path('network/reports/csv/', views.network_device_report_csv, name='network_device_report_csv'),
    path('network/reports/pdf/', views.network_device_report_pdf, name='network_device_report_pdf'),
    path('api/network/diagram/', views.network_diagram_api, name='network_diagram_api'),
    # Bandwidth Monitoring APIs
    path("api/bandwidth/summary/", views.bandwidth_summary_api, name="bandwidth_summary_api"),
    path("api/bandwidth/device/<int:device_id>/", views.device_bandwidth_api, name="device_bandwidth_api"),
    path("api/bandwidth/device/<int:device_id>/ip/", views.device_ip_bandwidth_api, name="device_ip_bandwidth_api"),
    path("api/bandwidth/device/<int:device_id>/report/csv/", views.bandwidth_report_csv, name="bandwidth_report_csv"),
    path("api/bandwidth/device/<int:device_id>/report/pdf/", views.bandwidth_report_pdf, name="bandwidth_report_pdf"),
    path("api/bandwidth/start/", views.start_bandwidth_monitoring_api, name="start_bandwidth_monitoring_api"),
    # CCTV Camera Management
    path("cctv/", views.cctv_dashboard, name="cctv_dashboard"),
    path("cctv/import/", views.import_cctv_xml, name="import_cctv_xml"),
    path("cctv/device/<int:device_id>/", views.cctv_device_detail, name="cctv_device_detail"),
    path("cctv/device/<int:device_id>/camera/<int:camera_number>/", views.cctv_camera_detail, name="cctv_camera_detail"),
    path("cctv/device/<int:device_id>/camera/<int:camera_number>/stream/", views.cctv_live_stream, name="cctv_live_stream"),
    path("cctv/device/<int:device_id>/camera/<int:camera_number>/snapshot/", views.cctv_snapshot, name="cctv_snapshot"),
    path("cctv/device/<int:device_id>/camera/<int:camera_number>/test/", views.cctv_test_connection, name="cctv_test_connection"),
    path("api/cctv/check/", views.check_cctv_status, name="check_cctv_status"),
    path("api/cctv/check-all/", views.check_all_cctv_status, name="check_all_cctv_status"),
    
    # DMSS Cloud Integration
    path("cctv/dmss/login/", views.dmss_login, name="dmss_login"),
    path("cctv/dmss/logout/", views.dmss_logout, name="dmss_logout"),
    path("cctv/dmss/status/", views.dmss_status, name="dmss_status"),
    path("cctv/dmss/devices/", views.dmss_devices, name="dmss_devices"),
    path("cctv/dmss/device/<str:device_id>/stream/", views.dmss_device_stream, name="dmss_device_stream"),
    path("cctv/dmss/device/<str:device_id>/snapshot/", views.dmss_device_snapshot, name="dmss_device_snapshot"),
    
    # DMSS Test Page
    path("cctv/dmss/test/", views.dmss_test_page, name="dmss_test_page"),
    
    # P2P Camera Access
    path("cctv/p2p/", views.p2p_camera_access, name="p2p_camera_access"),
    path("cctv/p2p/connect/", views.p2p_connect, name="p2p_connect"),
    path("cctv/p2p/stream/", views.p2p_stream, name="p2p_stream"),
    path("cctv/p2p/snapshot/", views.p2p_snapshot, name="p2p_snapshot"),
    path("api/isp/speed-test/", views.isp_speed_test_api, name="isp_speed_test_api"),
    
    # Metrics Monitoring APIs
    path('api/network/device/<int:device_id>/metrics/', api_views_metrics.device_metrics_api, name='device_metrics_api'),
    path('api/metrics/summary/', api_views_metrics.all_metrics_summary_api, name='all_metrics_summary_api'),
    path('api/network/device/<int:device_id>/metrics/refresh/', api_views_metrics.refresh_metrics_api, name='refresh_metrics_api'),
    
    # SSH Credentials Management
    path('ssh-credentials/', views_ssh_credentials.ssh_credentials_list, name='ssh_credentials_list'),
    path('ssh-credentials/create/', views_ssh_credentials.ssh_credential_create, name='ssh_credential_create'),
    path('ssh-credentials/create/<int:server_id>/', views_ssh_credentials.ssh_credential_create, name='ssh_credential_create_for_server'),
    path('ssh-credentials/<int:credential_id>/edit/', views_ssh_credentials.ssh_credential_edit, name='ssh_credential_edit'),
    path('ssh-credentials/<int:credential_id>/delete/', views_ssh_credentials.ssh_credential_delete, name='ssh_credential_delete'),
    path('ssh-credentials/<int:credential_id>/test/', views_ssh_credentials.ssh_credential_test, name='ssh_credential_test'),
    
    # Metrics Configuration
    path('metrics-config/', views_ssh_credentials.metrics_config_list, name='metrics_config_list'),
    path('metrics-config/<int:server_id>/edit/', views_ssh_credentials.metrics_config_edit, name='metrics_config_edit'),
    
    # Server Metrics APIs
    path('api/server/<int:server_id>/metrics/', views_ssh_credentials.server_metrics_api, name='server_metrics_api'),
    path('api/server/<int:server_id>/metrics/refresh/', views_ssh_credentials.refresh_server_metrics_api, name='refresh_server_metrics_api'),
    
    # Agent APIs
    path('api/agent/heartbeat/', agent_views.agent_heartbeat, name='agent_heartbeat'),
    path('agent/heartbeat/', agent_views.agent_heartbeat, name='agent_heartbeat_short'), # Added for agents hitting the shorter path
    path('api/agent/metrics/', agent_views.agent_metrics, name='agent_metrics'),
    path('api/agent/status/', agent_views.agent_status, name='agent_status'),
    path('api/agent/deploy/<int:server_id>/', agent_views.deploy_agent, name='deploy_agent'),
    path('api/agent/deploy-all/', agent_deployment_views.deploy_all_agents, name='deploy_all_agents'),
    path('api/agent/generate-tokens/', agent_deployment_views.generate_agent_tokens, name='generate_agent_tokens'),
    path('api/agent/deployment-status/', agent_deployment_views.agent_deployment_status, name='agent_deployment_status'),
    
    # Agent Deployment Interface
    path('agents/', agent_deployment_views.agent_deployment_dashboard, name='agent_deployment_dashboard'),
    path('deploy/agent/<int:server_id>/', agent_deployment_views.deploy_single_agent, name='deploy_single_agent'),
    path('restart/agent/<int:server_id>/', agent_deployment_views.restart_agent, name='restart_agent'),
    path('uninstall/agent/<int:server_id>/', agent_deployment_views.uninstall_agent, name='uninstall_agent'),
    path('check/agent/<int:server_id>/', agent_deployment_views.check_agent_status, name='check_agent_status'),
    path('dashboard-test/', views.dashboard_new_test, name='dashboard_new_test'),
    path('api/v2/metrics/server/<int:server_id>/detailed/', views.server_detailed_metrics_api, name='server_detailed_metrics_api'),
    path('api/servers/<int:server_id>/directories/', views.update_server_directories, name='update_server_directories'),
    path('ssl-certificates/', views.ssl_certificates_list, name='ssl_certificates_list'),
    
    # API endpoints
    path('api/', include(versioned_api_urls.urlpatterns)),
    
    # DTR Biometric Monitoring
    path('dtr-monitoring/', views.dtr_monitoring_dashboard, name='dtr_monitoring_dashboard'),
    
    # Infra Wiki
    path('infra-wiki/', views.infra_wiki, name='infra_wiki'),
]
