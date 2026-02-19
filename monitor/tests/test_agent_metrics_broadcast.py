
import pytest
import json
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
from monitor.models import Server
from django.test import TestCase

class AgentMetricsBroadcastTest(TestCase):
    def setUp(self):
        self.server = Server.objects.create(
            name="Broadcast Test Server",
            ip_address="127.0.0.1",
            agent_token="broadcast-token"
        )
        self.url = reverse('agent_metrics')

    @patch('monitor.agent_views.get_channel_layer')
    def test_agent_metrics_broadcast(self, mock_get_channel_layer):
        # Mock channel layer
        from unittest.mock import AsyncMock
        mock_channel_layer = MagicMock()
        mock_channel_layer.group_send = AsyncMock()
        mock_get_channel_layer.return_value = mock_channel_layer
        
        # Payload
        payload = {
            'server_id': 'Broadcast',
            'cpu': {'percent': 55.5, 'load_1m': 1.2},
            'memory': {'percent': 66.6},
            'disk': {'total': 100, 'used': 40},
            'system': {'uptime_seconds': 12345},
            'directory_metrics': [
                {'path': '/var/log', 'file_count': 100, 'size_mb': 50, 'status': 'ok'},
                {'path': '/var/www', 'file_count': 500, 'size_mb': 200, 'status': 'ok'}
            ]
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify broadcast was called
        mock_channel_layer.group_send.assert_called_once()
        args, kwargs = mock_channel_layer.group_send.call_args
        self.assertEqual(args[0], "status")
        self.assertEqual(args[1]["type"], "server.metrics")
        self.assertEqual(args[1]["server"]["id"], self.server.id)
        self.assertEqual(args[1]["server"]["last_cpu_percent"], 55.5)
        self.assertEqual(args[1]["server"]["last_disk_percent"], 40.0)
