from django.test import TestCase
from unittest.mock import patch, MagicMock
from monitor.models import Server, AlertRule, AlertState
from monitor.alerts import evaluate_alerts_for_server
from monitor.services.notification_service import NotificationService, EmailChannel

class NotificationServiceTests(TestCase):
    def test_email_channel_send(self):
        channel = EmailChannel()
        # Mock logger to avoid actual logging during test
        with patch('monitor.services.notification_service.logger') as mock_logger:
            result = channel.send("test@example.com", "Test Subject", "Test Message")
            self.assertTrue(result)
            mock_logger.info.assert_called()

    def test_notification_service_send(self):
        service = NotificationService()
        # Mock the channels
        service.channels['email'] = MagicMock()
        service.channels['email'].send.return_value = True
        
        results = service.send_notification(['email'], "test@example.com", "Subject", "Message")
        self.assertTrue(results['email'])
        service.channels['email'].send.assert_called_with("test@example.com", "Subject", "Message")

class AlertNotificationIntegrationTests(TestCase):
    def setUp(self):
        # Clear any default rules created by migrations
        AlertRule.objects.all().delete()
        
        self.server = Server.objects.create(
            name="Test Server",
            ip_address="192.168.1.100",
            enabled=True,
            last_status=Server.STATUS_UP,
            last_resource_checked=None # Ensure this doesn't trigger stale if logic changes
        )
        self.rule = AlertRule.objects.create(
            name="Server Down Rule",
            kind=AlertRule.KIND_SERVER_DOWN,
            severity=AlertRule.SEVERITY_CRIT,
            enabled=True,
            notification_channels=['email', 'console'],
            duration_seconds=0 # Should fire immediately on second pass
        )

    @patch('monitor.alerts.notification_service')
    def test_alert_triggers_notification(self, mock_notification_service):
        # Simulate server down
        self.server.last_status = Server.STATUS_DOWN
        self.server.save()
        
        # First pass: marks as pending
        evaluate_alerts_for_server(self.server)
        self.assertFalse(mock_notification_service.send_notification.called)
        
        # Second pass: fires alert
        evaluate_alerts_for_server(self.server)
        
        # Check if notification was sent
        self.assertTrue(mock_notification_service.send_notification.called)
        call_args = mock_notification_service.send_notification.call_args
        self.assertEqual(call_args[0][0], ['email', 'console'])
        self.assertIn("ALERT", call_args[0][2])
        self.assertIn("Test Server", call_args[0][2])

    @patch('monitor.alerts.notification_service')
    def test_alert_suppression(self, mock_notification_service):
        # Create a CPU High rule
        cpu_rule = AlertRule.objects.create(
            name="CPU High Rule",
            kind=AlertRule.KIND_CPU_HIGH,
            severity=AlertRule.SEVERITY_WARN,
            enabled=True,
            threshold=80.0,
            notification_channels=['console']
        )
        
        # Simulate Server DOWN and High CPU
        self.server.last_status = Server.STATUS_DOWN
        self.server.last_cpu_percent = 90.0
        self.server.save()
        
        # Two passes to trigger SERVER_DOWN
        evaluate_alerts_for_server(self.server)
        evaluate_alerts_for_server(self.server)
        
        # Verify notifications
        # Should call for SERVER_DOWN (ALERT)
        # Should NOT call for CPU_HIGH
        
        calls = mock_notification_service.send_notification.call_args_list
        titles = [call[0][2] for call in calls] # Extract subjects
        
        has_server_down = any("Server Down Rule" in t for t in titles)
        has_cpu_high = any("CPU High Rule" in t for t in titles)
        
        self.assertTrue(has_server_down, "Should fire Server Down alert")
        self.assertFalse(has_cpu_high, "Should suppress CPU High alert when Server Down")

    @patch('monitor.alerts.notification_service')
    def test_recovery_triggers_notification(self, mock_notification_service):
        # First put it in alert state
        self.server.last_status = Server.STATUS_DOWN
        self.server.save()
        
        evaluate_alerts_for_server(self.server) # Pending
        evaluate_alerts_for_server(self.server) # Active
        
        # Verify alert was sent
        self.assertTrue(mock_notification_service.send_notification.called)
        mock_notification_service.reset_mock()
        
        # Now recover
        self.server.last_status = Server.STATUS_UP
        self.server.save()
        
        evaluate_alerts_for_server(self.server)
        
        # Check if recovery notification was sent
        self.assertTrue(mock_notification_service.send_notification.called)
        call_args = mock_notification_service.send_notification.call_args
        self.assertIn("RECOVERY", call_args[0][2])
        self.assertIn("Test Server", call_args[0][2])
