from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator

from .models import Server, ISPConnection


class ServerForm(forms.ModelForm):
    class Meta:
        model = Server
        fields = [
            "name",
            "pinned",
            "tags",
            "server_type",
            "ip_address",
            "port",
            "use_https",
            "path",
            "http_check",
            "enabled",
        ]


class ISPConnectionForm(forms.ModelForm):
    class Meta:
        model = ISPConnection
        fields = [
            "name",
            "isp_type",
            "gateway_ip",
            "dns_servers",
            "bandwidth_mbps",
            "primary_connection",
            "enabled",
        ]
        widgets = {
            'dns_servers': forms.Textarea(attrs={'rows': 3, 'placeholder': '8.8.8.8, 1.1.1.1'}),
            'gateway_ip': forms.TextInput(attrs={'placeholder': '192.168.1.1'}),
            'bandwidth_mbps': forms.NumberInput(attrs={'min': 1}),
        }
        help_texts = {
            'dns_servers': 'Enter DNS server IP addresses separated by commas (e.g., 8.8.8.8, 1.1.1.1)',
            'gateway_ip': 'Gateway IP address of your ISP connection',
            'bandwidth_mbps': 'Expected bandwidth in Mbps (e.g., 100 for 100Mbps connection)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'placeholder': 'Main Office Converge'})
        self.fields['bandwidth_mbps'].validators.extend([
            MinValueValidator(1, message="Bandwidth must be at least 1 Mbps"),
            MaxValueValidator(10000, message="Bandwidth cannot exceed 10,000 Mbps")
        ])
    
    def clean_dns_servers(self):
        dns_servers = self.cleaned_data.get('dns_servers', '')
        if dns_servers:
            import re
            dns_list = [dns.strip() for dns in dns_servers.split(',') if dns.strip()]
            
            # Validate IP addresses
            ip_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
            
            for dns in dns_list:
                if not re.match(ip_pattern, dns):
                    raise forms.ValidationError(f"'{dns}' is not a valid IP address")
            
            return ', '.join(dns_list)
        
        return dns_servers
    
    def clean(self):
        cleaned_data = super().clean()
        primary = cleaned_data.get('primary_connection')
        enabled = cleaned_data.get('enabled')
        
        # If this is set as primary, ensure it's enabled
        if primary and not enabled:
            self.add_error('enabled', 'Primary ISP connection must be enabled')
        
        return cleaned_data
