from django.test import TestCase
from django.core.exceptions import ValidationError
from ..models import NetworkDevice

class NetworkDeviceModelTest(TestCase):
    def setUp(self):
        self.valid_data = {
            'name': 'Test Firewall',
            'device_type': 'FIREWALL',
            'ip_address': '192.168.1.1',
            'snmp_community': 'public',
            'snmp_port': 161,
            'api_username': 'test_user',
            'api_token': 'test123',
            'api_port': 443,
            'enabled': True
        }

    def test_create_valid_device(self):
        """Test creating a device with valid data"""
        device = NetworkDevice.objects.create(**self.valid_data)
        self.assertEqual(device.name, 'Test Firewall')
        self.assertEqual(device.get_device_type_display(), 'Firewall')

    def test_username_validation(self):
        """Test username validation rules"""
        invalid_usernames = [
            'a',  # too short
            'a' * 101,  # too long
            'admin!',  # invalid character
            'user@name',  # invalid character
            'user name',  # space not allowed
        ]
        
        for username in invalid_usernames:
            with self.subTest(username=username):
                with self.assertRaises(ValidationError):
                    device = NetworkDevice(**{**self.valid_data, 'api_username': username})
                    device.full_clean()

    def test_port_validation(self):
        """Test port number validation"""
        invalid_ports = [0, 65536, 99999]
        
        for port in invalid_ports:
            with self.subTest(port=port):
                with self.assertRaises(ValidationError):
                    device = NetworkDevice(**{**self.valid_data, 'api_port': port})
                    device.full_clean()

    def test_required_api_username_with_token(self):
        """Test that api_username is required when api_token is provided"""
        with self.assertRaises(ValidationError) as context:
            device = NetworkDevice(**{**self.valid_data, 'api_username': None})
            device.full_clean()
        self.assertIn('api_username', context.exception.error_dict)

    def test_required_snmp_community_with_port(self):
        """Test that snmp_community is required when snmp_port is set"""
        with self.assertRaises(ValidationError) as context:
            device = NetworkDevice(**{**self.valid_data, 'snmp_community': ''})
            device.full_clean()
        self.assertIn('snmp_community', context.exception.error_dict)

    def test_optional_fields(self):
        """Test that api_username and api_token are optional together"""
        try:
            device = NetworkDevice(
                name='Optional Fields Device',
                device_type='FIREWALL',
                ip_address='192.168.1.2',
                snmp_community='public',
                snmp_port=161
            )
            device.full_clean()  # Should not raise
            device.save()
        except ValidationError:
            self.fail("Optional fields validation failed")