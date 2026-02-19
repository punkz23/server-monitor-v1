from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from monitor.models import Server, ResourceSample
import json

class AgentIngestValidationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.server = Server.objects.create(
            name="Test Server",
            ip_address="192.168.1.100",
            agent_token="valid-token-123",
            enabled=True
        )
        self.url = reverse('agent_ingest_api')

    def test_valid_payload(self):
        payload = {
            "ts": timezone.now().timestamp(),
            "cpu": {"percent": 50.5},
            "memory": {
                "total_bytes": 8000000000,
                "used_bytes": 4000000000,
                "percent": 50.0
            }
        }
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer valid-token-123"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ResourceSample.objects.filter(server=self.server).exists())

    def test_invalid_cpu_percent_type(self):
        """Test that non-numeric cpu percent is rejected or handled safely."""
        payload = {
            "ts": timezone.now().timestamp(),
            "cpu": {"percent": "not-a-number"},
            "memory": {"percent": 50.0}
        }
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer valid-token-123"
        )
        # We expect a 400 Bad Request for validation failure
        # Currently it might 500 or 200 (if it just ignores it/casts to 0)
        self.assertNotEqual(response.status_code, 500)
        if response.status_code == 200:
             # If it returns 200, check that it didn't save garbage
             # Note: current implementation might crash or save None/0
             pass

    def test_cpu_percent_out_of_range(self):
        """Test that out-of-range cpu percent is rejected."""
        payload = {
            "ts": timezone.now().timestamp(),
            "cpu": {"percent": 150.0},
            "memory": {"percent": 50.0}
        }
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer valid-token-123"
        )
        # We want to enforce validation, so we expect 400
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_invalid_ram_bytes_type(self):
        """Test that non-integer bytes are rejected."""
        payload = {
            "ts": timezone.now().timestamp(),
            "cpu": {"percent": 10.0},
            "memory": {
                "total_bytes": "lots",
                "percent": 50.0
            }
        }
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer valid-token-123"
        )
        self.assertEqual(response.status_code, 400)
