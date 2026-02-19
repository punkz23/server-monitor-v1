from django.test import TestCase, Client
from django.urls import reverse
from monitor.models import Server

class DashboardViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create user
        # self.user = User.objects.create_user(username='admin', password='password')
        # self.client.login(username='admin', password='password') # If auth needed
        
        # Create servers with mix of valid IPs and hostnames
        Server.objects.create(name="Valid IP 1", ip_address="192.168.1.1", server_type="WEB")
        Server.objects.create(name="Valid IP 2", ip_address="10.0.0.1", server_type="WEB")
        Server.objects.create(name="Hostname 1", ip_address="example.com", server_type="WEB")
        Server.objects.create(name="Hostname 2", ip_address="http.example.com", server_type="WEB")

    def test_dashboard_view_no_crash(self):
        """Test that dashboard view renders without crashing on invalid IPs."""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Valid IP 1")
        self.assertContains(response, "Hostname 1")
