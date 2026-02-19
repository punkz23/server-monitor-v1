from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from monitor.models import NetworkDevice
from monitor.services.metrics_monitor_service import MetricsMonitorService
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["GET"])
def device_metrics_api(request, device_id):
    """API endpoint to get comprehensive device metrics with change tracking"""
    try:
        device = NetworkDevice.objects.get(id=device_id)
        
        # Only provide metrics for devices with SSH credentials
        monitored_ips = ['192.168.254.13', '192.168.254.50', '192.168.253.15']
        
        if device.ip_address not in monitored_ips:
            return JsonResponse({
                'success': False,
                'error': 'Metrics monitoring not available for this device'
            }, status=400)
        
        # Get metrics
        monitor = MetricsMonitorService()
        metrics_data = monitor.get_comprehensive_metrics(device.ip_address)
        
        if 'error' in metrics_data:
            return JsonResponse({
                'success': False,
                'error': metrics_data['error'],
                'timestamp': metrics_data.get('timestamp')
            }, status=500)
        
        return JsonResponse({
            'success': True,
            'device': {
                'id': device.id,
                'name': device.name,
                'ip_address': device.ip_address,
                'device_type': device.get_device_type_display()
            },
            'metrics': metrics_data['current'],
            'changes': metrics_data['changes'],
            'timestamp': metrics_data['timestamp'],
            'cached': metrics_data.get('cached', False)
        })
        
    except NetworkDevice.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Device not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error getting device metrics: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def all_metrics_summary_api(request):
    """API endpoint to get summary of all device metrics"""
    try:
        monitor = MetricsMonitorService()
        summary = monitor.get_all_metrics_summary()
        
        return JsonResponse({
            'success': True,
            'summary': summary,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting metrics summary: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def refresh_metrics_api(request, device_id):
    """API endpoint to force refresh metrics for a device"""
    try:
        device = NetworkDevice.objects.get(id=device_id)
        
        # Only allow refresh for monitored devices
        monitored_ips = ['192.168.254.13', '192.168.254.50', '192.168.253.15']
        
        if device.ip_address not in monitored_ips:
            return JsonResponse({
                'success': False,
                'error': 'Metrics refresh not available for this device'
            }, status=400)
        
        # Force refresh by clearing cache
        from django.core.cache import cache
        cache_key = f'device_metrics_{device.ip_address}'
        cache.delete(cache_key)
        
        # Get fresh metrics
        monitor = MetricsMonitorService()
        metrics_data = monitor.get_comprehensive_metrics(device.ip_address)
        
        if 'error' in metrics_data:
            return JsonResponse({
                'success': False,
                'error': metrics_data['error']
            }, status=500)
        
        return JsonResponse({
            'success': True,
            'message': 'Metrics refreshed successfully',
            'metrics': metrics_data['current'],
            'changes': metrics_data['changes'],
            'timestamp': metrics_data['timestamp']
        })
        
    except NetworkDevice.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Device not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error refreshing metrics: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
