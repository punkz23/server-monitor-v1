from django.test import TestCase
from django.contrib.staticfiles import finders

class FrontendAssetsTests(TestCase):
    def test_apexcharts_exists(self):
        """
        Verify that ApexCharts library is present in static files.
        """
        result = finders.find('js/vendor/apexcharts.min.js')
        self.assertIsNotNone(result, "ApexCharts library not found in static files")
