# SSH Credentials Management URLs
from django.urls import path
from . import views_ssh_credentials

urlpatterns = [
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
    
    # API Endpoints
    path('api/server/<int:server_id>/metrics/', views_ssh_credentials.server_metrics_api, name='server_metrics_api'),
    path('api/server/<int:server_id>/metrics/refresh/', views_ssh_credentials.refresh_server_metrics_api, name='refresh_server_metrics_api'),
]
