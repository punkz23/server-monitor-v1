from django.urls import path
from . import agent_views

app_name = 'agent'

urlpatterns = [
    path('heartbeat/', agent_views.agent_heartbeat, name='agent_heartbeat'),
    path('metrics/', agent_views.agent_metrics, name='agent_metrics'),
    path('status/', agent_views.agent_status, name='agent_status'),
    path('deploy/<int:server_id>/', agent_views.deploy_agent, name='deploy_agent'),
]
