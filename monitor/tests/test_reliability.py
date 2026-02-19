import logging
from django.test import TestCase
from unittest.mock import patch, MagicMock
from monitor.models import Server
from monitor.services.server_status_monitor import ServerStatusMonitor
import requests # Needed for exceptions
import urllib3 # For InsecureRequestWarning category

class ServerStatusReliabilityTest(TestCase):
    def setUp(self):
        # Create a server that uses HTTPS and *doesn't* skip SSL verification
        self.server_https_verified = Server.objects.create(
            name='Secure HTTPS Server',
            ip_address='192.168.1.102',
            enabled=True,
            use_https=True,
            skip_ssl_verification=False
        )
        # Create a server that uses HTTPS and *does* skip SSL verification
        self.server_https_unverified = Server.objects.create(
            name='Unverified HTTPS Server',
            ip_address='192.168.1.103',
            enabled=True,
            use_https=True,
            skip_ssl_verification=True
        )
        self.monitor = ServerStatusMonitor()

    @patch('monitor.services.server_status_monitor.requests.get')
    def test_https_verification_argument(self, mock_requests_get):
        # --- Test for server_https_verified (should attempt verify=True) ---
        mock_requests_get.reset_mock() # Clear previous calls
        mock_requests_get.side_effect = [
            requests.exceptions.RequestException("Simulated HTTP failure"), # First call for HTTP check
            MagicMock(status_code=200) # Second call for HTTPS check
        ]
        
        is_up, method = self.monitor.check_server_status(self.server_https_verified)
        
        https_call_found = False
        for call_args, call_kwargs in mock_requests_get.call_args_list:
            if call_args[0].startswith('https://'):
                https_call_found = True
                # For server_https_verified, 'verify' should be True or omitted
                self.assertFalse(call_kwargs.get('verify') is False, 
                                 "Verified HTTPS request should not explicitly skip verification (verify=False).")
                break
        self.assertTrue(https_call_found, "Expected an HTTPS call to be made for verified server.")

        # --- Test for server_https_unverified (should attempt verify=False) ---
        mock_requests_get.reset_mock() # Clear previous calls
        mock_requests_get.side_effect = [
            requests.exceptions.RequestException("Simulated HTTP failure"), # First call for HTTP check
            MagicMock(status_code=200) # Second call for HTTPS check
        ]
        
        is_up, method = self.monitor.check_server_status(self.server_https_unverified)
        
        https_call_found = False
        for call_args, call_kwargs in mock_requests_get.call_args_list:
            if call_args[0].startswith('https://'):
                https_call_found = True
                # For server_https_unverified, 'verify' should be False
                self.assertTrue(call_kwargs.get('verify') is False, 
                                "Unverified HTTPS request should explicitly skip verification (verify=False).")
                break
        self.assertTrue(https_call_found, "Expected an HTTPS call to be made for unverified server.")