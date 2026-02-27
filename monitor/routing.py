from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path("ws/status/", consumers.StatusConsumer.as_asgi()),
    path("ws/monitoring/", consumers.MonitoringConsumer.as_asgi()),
    path("ws/terminal/", consumers.TerminalConsumer.as_asgi()),
]
