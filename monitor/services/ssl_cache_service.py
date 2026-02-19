from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

def get_cached_ssl_certificates():
    """Get SSL certificates with caching to improve performance"""
    cache_key = 'ssl_certificates_all'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        logger.info("SSL certificates retrieved from cache")
        return cached_data
    
    # Cache miss - get fresh data
    logger.info("SSL certificates cache miss - fetching fresh data")
    from monitor.views import get_ssl_certificates_for_device
    from monitor.models import NetworkDevice
    from monitor.services.server_status_monitor import ServerStatusMonitor
    
    ssl_certificates = {}
    ssl_summary = {
        'total': 0,
        'good': 0,
        'warning': 0,
        'critical': 0,
        'expired': 0,
        'error': 0
    }
    
    # Get SSL devices
    network_devices = NetworkDevice.objects.filter(enabled=True, device_type__in=['WEB_SERVER', 'ROUTER'])
    status_monitor = ServerStatusMonitor()
    
    for device in network_devices:
        # Skip SSL check if server is down
        is_reachable = status_monitor.check_server_status(device.ip_address)
        if not is_reachable:
            logger.info(f"Skipping SSL check for {device.name} ({device.ip_address}) - server is down")
            # Add error entry for down server
            ssl_certificates[device.id] = {
                'hostname': device.ip_address,
                'port': '443',
                'status': 'error',
                'status_color': '#6c757d',
                'error': 'Server is down - SSL check skipped',
                'days_remaining': 0,
                'subject_common_name': 'N/A',
                'issuer_common_name': 'N/A',
                'expiry_date': 'N/A',
                'connection_method': 'skipped'
            }
            ssl_summary['total'] += 1
            ssl_summary['error'] += 1
            continue
        
        # Server is up - perform SSL check
        device_ssl = get_ssl_certificates_for_device(device)
        if device_ssl:
            ssl_certificates[device.id] = device_ssl
            ssl_summary['total'] += len(device_ssl)
            
            # Count certificate statuses
            for port, cert in device_ssl.items():
                status = cert.get('status', 'error')
                if status in ssl_summary:
                    ssl_summary[status] += 1
    
    # Cache for 5 minutes
    cache.set(cache_key, {
        'ssl_certificates': ssl_certificates,
        'ssl_summary': ssl_summary,
        'timestamp': timezone.now().isoformat()
    }, timeout=300)
    
    return ssl_certificates, ssl_summary

def update_ssl_certificate_cache():
    """Background task to update SSL certificate cache"""
    logger.info("Updating SSL certificate cache in background")
    get_cached_ssl_certificates()  # This will refresh the cache
    logger.info("SSL certificate cache updated")
