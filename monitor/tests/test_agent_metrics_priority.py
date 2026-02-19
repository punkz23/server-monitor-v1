
from django.test import TestCase
from unittest.mock import MagicMock, patch
from django.utils import timezone
from datetime import timedelta
from monitor.models import Server
from monitor.models_metrics import ServerMetrics
from monitor.services.metrics_monitor_service import MetricsMonitorService

class TestAgentMetricsPriority(TestCase):
    def setUp(self):
        self.server = Server.objects.create(
            name="Test Server",
            ip_address="127.0.0.1",
            agent_token="test-token"
        )
        self.service = MetricsMonitorService()

    @patch('paramiko.SSHClient')
    def test_prioritize_recent_agent_metrics(self, mock_ssh):
        # Create recent agent metrics (2 minutes ago)
        now = timezone.now()
        recent_metrics = ServerMetrics.objects.create(
            server=self.server,
            timestamp=now - timedelta(minutes=2),
            agent_server_id="test-agent",
            cpu_percent=45.5,
            memory_percent=60.2,
            disk_percent=30.0,
            uptime_seconds=3600,
            directory_metrics=[
                {'path': '/var/log', 'file_count': 100, 'size_mb': 50, 'status': 'ok'}
            ]
        )
        self.server.last_agent_metrics = recent_metrics.timestamp
        self.server.save()

        # Call the service
        metrics = self.service.get_comprehensive_metrics(self.server.ip_address, server=self.server)

        # Verify agent metrics are used
        self.assertIn('current', metrics)
        self.assertEqual(metrics['current']['cpu']['usage_percent'], 45.5)
        self.assertEqual(metrics['current']['ram']['usage_percent'], 60.2)
        self.assertEqual(metrics['current']['disk']['usage_percent'], 30.0)
        self.assertEqual(metrics['source'], 'agent')
        self.assertIn('directory_watch', metrics['current'])
        self.assertEqual(metrics['current']['directory_watch'][0]['path'], '/var/log')
        self.assertEqual(metrics['current']['directory_watch'][0]['file_count'], 100)
        self.assertEqual(metrics['current']['directory_watch'][0]['size_mb'], 50)
        
        # Verify SSH was NOT called
        mock_ssh.assert_not_called()

    @patch('paramiko.SSHClient')
    def test_fallback_to_ssh_when_agent_metrics_stale(self, mock_ssh):
        # Mock SSH response
        mock_ssh_instance = mock_ssh.return_value
        mock_ssh_instance.exec_command.return_value = (None, MagicMock(read=lambda: b"10.5\n"), None)
        
        # Create stale agent metrics (15 minutes ago)
        now = timezone.now()
        stale_metrics = ServerMetrics.objects.create(
            server=self.server,
            timestamp=now - timedelta(minutes=15),
            agent_server_id="test-agent",
            cpu_percent=45.5
        )
        self.server.last_agent_metrics = stale_metrics.timestamp
        self.server.save()

        # Mock SSH credentials exist
        with patch.object(MetricsMonitorService, 'load_ssh_credentials') as mock_load:
            self.service.ssh_credentials[self.server.ip_address] = {
                'username': 'test', 'password': 'test', 'port': 22
            }
            
            # Call the service
            metrics = self.service.get_comprehensive_metrics(self.server.ip_address, server=self.server)

        # Verify SSH was used (mocked response returns 10.5 for CPU)
        self.assertIn('current', metrics)
        self.assertTrue(mock_ssh.called)
        self.assertNotEqual(metrics.get('source'), 'agent')

    def test_get_performance_trend(self):
        # Create agent metrics
        now = timezone.now()
        ServerMetrics.objects.create(
            server=self.server,
            timestamp=now - timedelta(minutes=10),
            agent_server_id="test-agent",
            cpu_percent=40.0,
            memory_percent=50.0,
            network_bytes_recv=1000,
            network_bytes_sent=2000
        )
        
        # Create a check result for latency
        from monitor.models import CheckResult
        CheckResult.objects.create(
            server=self.server,
            status='UP',
            latency_ms=15,
            checked_at=now - timedelta(minutes=5)
        )
        
        trend = self.service.get_performance_trend(self.server, hours=1)
        
        self.assertEqual(trend['source'], 'agent')
        self.assertEqual(len(trend['cpu']), 1)
        self.assertEqual(trend['cpu'][0]['y'], 40.0)
        self.assertEqual(len(trend['latency']), 1)
        self.assertEqual(trend['latency'][0]['y'], 15)
        self.assertIn('network_in', trend)
        self.assertIn('network_out', trend)

