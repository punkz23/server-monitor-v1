from django.test import TestCase
from unittest.mock import patch, MagicMock
from monitor.models import Server
from monitor.services.server_status_monitor import ServerStatusMonitor
import time

class ServerStatusBottleneckTest(TestCase):
    def setUp(self):
        # Create 5 servers
        for i in range(5):
            Server.objects.create(
                name=f'Server {i}',
                ip_address=f'192.168.1.{i+10}',
                enabled=True
            )
        self.monitor = ServerStatusMonitor()

    @patch('monitor.services.server_status_monitor.requests.get')
    def test_update_performance(self, mock_requests):
        # Simulate network latency of 0.5s per successful check
        def slow_success(*args, **kwargs):
            time.sleep(0.5)
            resp = MagicMock()
            resp.status_code = 200
            return resp
        
        mock_requests.side_effect = slow_success
        
        start_time = time.time()
        self.monitor.update_all_server_status()
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"\nProcessing 5 servers with 0.5s latency took {duration:.2f}s")
        
        # If the implementation is sequential, it will take at least 5 * 0.5 = 2.5 seconds.
        # We assert that it should be faster (e.g. < 1.5s) to fail if sequential.
        self.assertLess(duration, 1.5, "Bottleneck detected: Server updates are too slow (likely sequential)")
