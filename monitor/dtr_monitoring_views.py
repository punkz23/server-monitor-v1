from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg, Count, Q, F
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from datetime import timedelta
import json
from .models import DTRBiometricMetrics, DTRPunchSession, DTRDevicePerformance, DTRLocationMetrics


@require_http_methods(["GET"])
def dtr_accuracy_friction_panel(request):
    """Core metrics panel - most important for user experience"""
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    
    # Calculate core metrics
    sessions = DTRPunchSession.objects.filter(timestamp__gte=last_24h)
    total_sessions = sessions.count()
    
    if total_sessions == 0:
        return JsonResponse({
            'status': 'success',
            'data': {
                'false_rejection_rate': 0,
                'retry_count_avg': 0,
                'liveness_failures': 0,
                'manual_override_rate': 0,
                'total_sessions': 0,
                'critical_thresholds': {
                    'frr_threshold': 2.0,
                    'retry_threshold': 1.5,
                    'manual_override_threshold': 5.0
                }
            }
        })
    
    # False Rejection Rate (valid employees rejected)
    failed_sessions = sessions.filter(success=False).exclude(
        error_type__in=['network_error', 'api_error', 'server_error']
    ).count()
    false_rejection_rate = (failed_sessions / total_sessions) * 100
    
    # Average retry count
    retry_count_avg = sessions.aggregate(avg_attempts=Avg('attempts_count'))['avg_attempts'] or 1.0
    
    # Liveness failures
    liveness_failures = sessions.filter(liveness_passed=False).count()
    
    # Manual override rate
    manual_overrides = sessions.filter(manual_override_required=True).count()
    manual_override_rate = (manual_overrides / total_sessions) * 100
    
    return JsonResponse({
        'status': 'success',
        'data': {
            'false_rejection_rate': round(false_rejection_rate, 2),
            'retry_count_avg': round(retry_count_avg, 2),
            'liveness_failures': liveness_failures,
            'manual_override_rate': round(manual_override_rate, 2),
            'total_sessions': total_sessions,
            'critical_thresholds': {
                'frr_threshold': 2.0,
                'retry_threshold': 1.5,
                'manual_override_threshold': 5.0
            },
            'alerts': {
                'frr_critical': false_rejection_rate > 2.0,
                'retry_critical': retry_count_avg > 1.5,
                'manual_override_critical': manual_override_rate > 5.0,
                'liveness_spike': liveness_failures > (total_sessions * 0.01)  # 1% threshold
            }
        }
    })


@require_http_methods(["GET"])
def dtr_performance_latency_panel(request):
    """Performance and latency metrics"""
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    
    sessions = DTRPunchSession.objects.filter(
        timestamp__gte=last_24h,
        success=True
    )
    
    # Recognition latency targets: <2s on 4G, <1s on WiFi
    wifi_sessions = sessions.filter(network_type='WiFi')
    mobile_sessions = sessions.filter(network_type__in=['4G', '5G'])
    
    wifi_latency = wifi_sessions.aggregate(
        avg_time=Avg('recognition_time')
    )['avg_time'] or 0
    
    mobile_latency = mobile_sessions.aggregate(
        avg_time=Avg('recognition_time')
    )['avg_time'] or 0
    
    # App startup time
    startup_time = sessions.aggregate(
        avg_time=Avg('startup_time')
    )['avg_time'] or 0
    
    # Frame drop rate (jank) - would need to be tracked in mobile app
    frame_drop_rate = 2.5  # Placeholder - would come from mobile metrics
    
    # Battery drain per punch
    battery_drain = sessions.exclude(
        battery_level_before__isnull=True,
        battery_level_after__isnull=True
    ).aggregate(
        avg_drain=Avg(F('battery_level_before') - F('battery_level_after'))
    )['avg_drain'] or 0
    
    return JsonResponse({
        'status': 'success',
        'data': {
            'recognition_latency': {
                'wifi_avg': round(wifi_latency, 2),
                'mobile_avg': round(mobile_latency, 2),
                'wifi_target': 1000,  # 1 second
                'mobile_target': 2000,  # 2 seconds
                'wifi_performance': 'good' if wifi_latency < 1000 else 'poor',
                'mobile_performance': 'good' if mobile_latency < 2000 else 'poor'
            },
            'app_startup_time': round(startup_time, 2),
            'frame_drop_rate': frame_drop_rate,
            'battery_drain_per_punch': round(battery_drain, 2),
            'performance_targets': {
                'startup_target': 3000,  # 3 seconds
                'frame_drop_target': 5.0,  # 5%
                'battery_drain_target': 1.0  # 1% per punch
            }
        }
    })


@require_http_methods(["GET"])
def dtr_environmental_hardware_panel(request):
    """Device and location-based metrics"""
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    
    sessions = DTRPunchSession.objects.filter(timestamp__gte=last_24h)
    
    # Failure by device model
    device_failures = {}
    device_sessions = sessions.values('device_model').annotate(
        total=Count('id'),
        failed=Count('id', filter=Q(success=False))
    ).order_by('-total')
    
    for device in device_sessions:
        failure_rate = (device['failed'] / device['total']) * 100 if device['total'] > 0 else 0
        device_failures[device['device_model']] = {
            'total_sessions': device['total'],
            'failed_sessions': device['failed'],
            'failure_rate': round(failure_rate, 2)
        }
    
    # Failure by location
    location_failures = {}
    location_sessions = sessions.values('location_name').annotate(
        total=Count('id'),
        failed=Count('id', filter=Q(success=False)),
        avg_distance=Avg('geofence_distance')
    ).order_by('-total')
    
    for location in location_sessions:
        failure_rate = (location['failed'] / location['total']) * 100 if location['total'] > 0 else 0
        location_failures[location['location_name']] = {
            'total_sessions': location['total'],
            'failed_sessions': location['failed'],
            'failure_rate': round(failure_rate, 2),
            'avg_geofence_distance': round(location['avg_distance'] or 0, 2)
        }
    
    # OS version distribution
    os_distribution = sessions.values('os_version').annotate(
        count=Count('id')
    ).order_by('-count')
    
    return JsonResponse({
        'status': 'success',
        'data': {
            'device_failures': device_failures,
            'location_failures': location_failures,
            'os_distribution': list(os_distribution),
            'problematic_devices': [
                device for device, data in device_failures.items() 
                if data['failure_rate'] > 10  # Devices with >10% failure rate
            ],
            'problematic_locations': [
                location for location, data in location_failures.items() 
                if data['failure_rate'] > 10  # Locations with >10% failure rate
            ]
        }
    })


@require_http_methods(["GET"])
def dtr_operational_security_panel(request):
    """Operational and security metrics"""
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    
    sessions = DTRPunchSession.objects.filter(timestamp__gte=last_24h)
    
    # Geofence precision
    geofence_distances = sessions.exclude(geofence_distance__isnull=True).values_list('geofence_distance', flat=True)
    avg_geofence_distance = sum(geofence_distances) / len(geofence_distances) if geofence_distances else 0
    
    # Sync lag
    sync_lags = sessions.exclude(sync_lag__isnull=True).values_list('sync_lag', flat=True)
    avg_sync_lag = sum(sync_lags) / len(sync_lags) if sync_lags else 0
    
    # API error rates
    total_sessions = sessions.count()
    api_errors = sessions.filter(error_type__in=['api_error', 'server_error']).count()
    api_error_rate = (api_errors / total_sessions) * 100 if total_sessions > 0 else 0
    
    # Security metrics
    liveness_attempts = sessions.count()
    liveness_failures = sessions.filter(liveness_passed=False).count()
    spoofing_attempts = sessions.filter(error_type='spoofing_detected').count()
    
    return JsonResponse({
        'status': 'success',
        'data': {
            'geofence_precision': {
                'avg_distance': round(avg_geofence_distance, 2),
                'target_distance': 50.0,  # 50 meters
                'precision_status': 'good' if avg_geofence_distance < 50 else 'needs_improvement'
            },
            'sync_performance': {
                'avg_sync_lag': round(avg_sync_lag, 2),
                'target_sync_lag': 30.0,  # 30 seconds
                'sync_status': 'good' if avg_sync_lag < 30 else 'slow'
            },
            'api_health': {
                'error_rate': round(api_error_rate, 2),
                'total_errors': api_errors,
                'total_requests': total_sessions,
                'health_status': 'healthy' if api_error_rate < 5 else 'degraded'
            },
            'security_metrics': {
                'liveness_success_rate': round(((liveness_attempts - liveness_failures) / liveness_attempts) * 100, 2) if liveness_attempts > 0 else 100,
                'spoofing_attempts_detected': spoofing_attempts,
                'total_liveness_checks': liveness_attempts,
                'security_status': 'secure' if spoofing_attempts == 0 else 'alert'
            }
        }
    })


@require_http_methods(["GET"])
def dtr_heatmap_data(request):
    """Generate heatmap data for office locations"""
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    
    # Group by location and calculate average time to punch
    location_data = DTRPunchSession.objects.filter(
        timestamp__gte=last_24h,
        success=True
    ).values('location_name').annotate(
        avg_punch_time=Avg('total_session_time'),
        total_punches=Count('id'),
        failure_rate=Count('id', filter=Q(success=False)) * 100.0 / Count('id')
    ).order_by('location_name')
    
    heatmap_data = []
    for location in location_data:
        heatmap_data.append({
            'location': location['location_name'],
            'avg_time_to_punch': round(location['avg_punch_time'] or 0, 2),
            'total_punches': location['total_punches'],
            'failure_rate': round(location['failure_rate'], 2),
            'performance_color': _get_performance_color(location['avg_punch_time'] or 0)
        })
    
    return JsonResponse({
        'status': 'success',
        'data': heatmap_data
    })


def _get_performance_color(avg_time):
    """Get color based on performance"""
    if avg_time < 2000:  # Under 2 seconds
        return '#4CAF50'  # Green
    elif avg_time < 5000:  # Under 5 seconds
        return '#FF9800'  # Orange
    else:
        return '#F44336'  # Red


@csrf_exempt
@require_http_methods(["POST"])
def dtr_ingest_mobile_metrics(request):
    """Ingest metrics from mobile app"""
    try:
        print(f"Raw request body: {request.body}")  # Debug line
        data = json.loads(request.body)
        print(f"Parsed data: {data}")  # Debug line
        
        # Create punch session record
        session = DTRPunchSession.objects.create(
            session_id=data.get('session_id'),
            employee_id=data.get('employee_id'),
            punch_type=data.get('punch_type'),
            device_model=data.get('device_model'),
            os_version=data.get('os_version'),
            app_version=data.get('app_version'),
            startup_time=data.get('startup_time'),
            camera_ready_time=data.get('camera_ready_time'),
            face_detection_time=data.get('face_detection_time'),
            recognition_time=data.get('recognition_time'),
            total_session_time=data.get('total_session_time'),
            attempts_count=data.get('attempts_count', 1),
            confidence_score=data.get('confidence_score'),
            liveness_passed=data.get('liveness_passed', True),
            face_detected=data.get('face_detected', True),
            location_name=data.get('location_name'),
            geofence_distance=data.get('geofence_distance'),
            network_type=data.get('network_type'),
            battery_level_before=data.get('battery_level_before'),
            battery_level_after=data.get('battery_level_after'),
            success=data.get('success', False),
            error_type=data.get('error_type'),
            error_message=data.get('error_message'),
            manual_override_required=data.get('manual_override_required', False),
            local_timestamp=parse_datetime(data.get('local_timestamp')) if data.get('local_timestamp') else timezone.now(),
        )
        
        # Calculate sync lag
        if session.local_timestamp:
            sync_lag = (timezone.now() - session.local_timestamp).total_seconds()
            session.sync_lag = sync_lag
            session.save()
        
        # Update device performance aggregates
        device_perf, created = DTRDevicePerformance.objects.get_or_create(
            device_model=data.get('device_model'),
            os_version=data.get('os_version'),
            defaults={
                'total_sessions': 1,
                'successful_sessions': 1 if data.get('success') else 0,
                'failed_sessions': 0 if data.get('success') else 1,
            }
        )
        
        if not created:
            device_perf.total_sessions += 1
            if data.get('success'):
                device_perf.successful_sessions += 1
            else:
                device_perf.failed_sessions += 1
            device_perf.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Metrics ingested successfully',
            'session_id': session.session_id
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)


@require_http_methods(["GET"])
def dtr_dashboard_overview(request):
    """Get all dashboard data in one call"""
    try:
        accuracy_data = dtr_accuracy_friction_panel(request)
        performance_data = dtr_performance_latency_panel(request)
        environmental_data = dtr_environmental_hardware_panel(request)
        operational_data = dtr_operational_security_panel(request)
        heatmap_data = dtr_heatmap_data(request)
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'accuracy_friction': json.loads(accuracy_data.content)['data'],
                'performance_latency': json.loads(performance_data.content)['data'],
                'environmental_hardware': json.loads(environmental_data.content)['data'],
                'operational_security': json.loads(operational_data.content)['data'],
                'heatmap': json.loads(heatmap_data.content)['data']
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
