import logging
from django.test import TestCase
from unittest.mock import patch, MagicMock
from monitor.models import Server
from monitor.services.server_status_monitor import ServerStatusMonitor

class MonitoringLoggingTest(TestCase):
    def setUp(self):
        self.server = Server.objects.create(
            name='Log Test Server',
            ip_address='192.168.1.100',
            enabled=True,
            last_status=Server.STATUS_DOWN # Start as DOWN so UP is a change
        )
        self.monitor = ServerStatusMonitor()

    @patch('monitor.services.server_status_monitor.requests.get')
    def test_detailed_logging(self, mock_get):
        mock_get.return_value.status_code = 200
        
        # We expect the log to contain details about the check method
        with self.assertLogs('monitor.services.server_status_monitor', level='INFO') as cm:
            self.monitor.update_all_server_status()
            
        # This assertion should fail with current implementation
        found_method_log = any('Method: HTTP' in log for log in cm.output)
        self.assertTrue(found_method_log, "Log should contain the check method (HTTP)")
