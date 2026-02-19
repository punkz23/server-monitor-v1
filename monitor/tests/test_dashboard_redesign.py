from django.test import TestCase
from django.template.loader import get_template
from django.template import TemplateDoesNotExist

class DashboardRedesignTemplateTests(TestCase):
    def test_new_dashboard_template_exists(self):
        """
        Verify that the new dashboard template exists.
        """
        try:
            get_template('monitor/dashboard_new.html')
        except TemplateDoesNotExist:
            self.fail("monitor/dashboard_new.html template does not exist")

    def test_new_dashboard_structure(self):
        """
        Verify that the new dashboard template has the required hybrid layout elements.
        """
        template = get_template('monitor/dashboard_new.html')
        # We render with dummy context to check for elements
        content = template.render({'servers_by_type': {'Test': []}})
        
        self.assertIn('id="dashboard-container"', content)
        self.assertIn('class="category-tabs"', content)
        self.assertIn('class="server-grid"', content)
        
        # Side Panel Elements
        self.assertIn('id="side-panel"', content)
        self.assertIn('class="panel-close"', content)
        self.assertIn('id="panel-server-name"', content)
        self.assertIn('id="metrics-charts"', content)

    def test_dashboard_new_test_view(self):
        """
        Verify that the temporary test view returns a 200 OK and uses the correct template.
        """
        from django.urls import reverse
        from monitor.models import Server
        
        # Create test servers with different types using correct constants
        Server.objects.create(name='Web Server 1', ip_address='192.168.1.1', server_type=Server.TYPE_WEB, enabled=True)
        Server.objects.create(name='DB Server 1', ip_address='192.168.1.2', server_type=Server.TYPE_DB, enabled=True)
        Server.objects.create(name='Storage 1', ip_address='192.168.1.3', server_type=Server.TYPE_FILE, enabled=True)

        response = self.client.get(reverse('dashboard_new_test'))
        if response.status_code == 302:
            from django.contrib.auth.models import User
            user = User.objects.create_user(username='testuser', password='password')
            self.client.login(username='testuser', password='password')
            response = self.client.get(reverse('dashboard_new_test'))
            
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'monitor/dashboard_new.html')
        
        # Verify grouping in context (using display names)
        servers_by_type = response.context['servers_by_type']
        self.assertIn('Web server', servers_by_type)
        self.assertIn('DB server', servers_by_type)
        self.assertIn('File server', servers_by_type)
        self.assertEqual(len(servers_by_type['Web server']), 1)
        self.assertEqual(len(servers_by_type['DB server']), 1)
        self.assertEqual(len(servers_by_type['File server']), 1)

    def test_main_dashboard_uses_new_template(self):
        """
        Verify that the main dashboard view now uses the redesigned template.
        """
        from django.urls import reverse
        response = self.client.get(reverse('dashboard'))
        
        # Handle possible redirect
        if response.status_code == 302:
            from django.contrib.auth.models import User
            user, _ = User.objects.get_or_create(username='testuser2', password='password')
            self.client.login(username='testuser2', password='password')
            response = self.client.get(reverse('dashboard'))
            
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'monitor/dashboard_new.html')

    def test_server_detailed_metrics_api(self):
        """
        Verify the API endpoint for detailed server metrics.
        """
        from django.urls import reverse
        from monitor.models import Server
        
        server = Server.objects.create(name='API Test Server', ip_address='127.0.0.1', enabled=True)
        
        # New URL: 'server_detailed_metrics_api'
        url = reverse('server_detailed_metrics_api', kwargs={'server_id': server.id})
        self.assertEqual(url, f'/api/v2/metrics/server/{server.id}/detailed/')
        
        response = self.client.get(url)
        # Handle possible redirect
        if response.status_code == 302:
            from django.contrib.auth.models import User
            User.objects.get_or_create(username='testuser3', password='password')
            self.client.login(username='testuser3', password='password')
            response = self.client.get(url)
            
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertIn('metrics', data)
        self.assertIn('historical', data)
        self.assertIn('ssl', data)
        self.assertIn('directory_watch', data)
        self.assertIn('services', data)

    def test_dashboard_performance_benchmark(self):
        """
        Verify that the dashboard loads within the target time (< 200ms).
        """
        import time
        from django.urls import reverse
        from django.contrib.auth.models import User
        
        # Ensure we are logged in
        User.objects.get_or_create(username='testuser4', password='password')
        self.client.login(username='testuser4', password='password')
        
        url = reverse('dashboard')
        
        start_time = time.time()
        response = self.client.get(url)
        end_time = time.time()
        
        load_time_ms = (end_time - start_time) * 1000
        
        self.assertEqual(response.status_code, 200)
        # Target is < 200ms. In test environment, it might be slightly different, 
        # but we use it as a benchmark.
        self.assertLess(load_time_ms, 200, f"Dashboard load time too high: {load_time_ms:.2f}ms")
