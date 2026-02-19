"""
SSH Credentials Management Views
Provides UI for managing SSH credentials and server metrics configuration
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.utils import timezone
import paramiko
import logging

from monitor.models import Server
from monitor.models_ssh_credentials import SSHCredential, ServerMetricsConfig
from monitor.services.metrics_monitor_service import MetricsMonitorService

logger = logging.getLogger(__name__)


@login_required
def ssh_credentials_list(request):
    """List all SSH credentials"""
    credentials = SSHCredential.objects.select_related('server').all()
    
    context = {
        'credentials': credentials,
        'title': 'SSH Credentials Management'
    }
    
    return render(request, 'monitor/ssh_credentials_list.html', context)


@login_required
def ssh_credential_create(request, server_id=None):
    """Create new SSH credential"""
    server = None
    if server_id:
        server = get_object_or_404(Server, id=server_id)
    
    if request.method == 'POST':
        try:
            # Get form data
            server_id = request.POST.get('server')
            username = request.POST.get('username')
            password = request.POST.get('password')
            port = request.POST.get('port', 22)
            private_key_path = request.POST.get('private_key_path', '')
            is_active = request.POST.get('is_active') == 'on'
            
            # Get server object
            server = get_object_or_404(Server, id=server_id)
            
            # Check if credential already exists for this server
            existing = SSHCredential.objects.filter(server=server).first()
            if existing:
                messages.warning(request, f'SSH credential already exists for {server.name}. Please edit the existing one.')
                return redirect('ssh_credential_edit', credential_id=existing.id)
            
            # Create credential
            credential = SSHCredential(
                server=server,
                username=username,
                port=port,
                private_key_path=private_key_path,
                is_active=is_active
            )
            credential.set_password(password)
            credential.save()
            
            messages.success(request, f'SSH credential created for {server.name}')
            return redirect('ssh_credentials_list')
            
        except Exception as e:
            messages.error(request, f'Error creating SSH credential: {str(e)}')
    
    # Get servers for dropdown
    servers = Server.objects.all()
    
    context = {
        'title': 'Create SSH Credential',
        'server': server,
        'servers': servers,
        'action': 'create'
    }
    
    return render(request, 'monitor/ssh_credential_form.html', context)


@login_required
def ssh_credential_edit(request, credential_id):
    """Edit existing SSH credential"""
    credential = get_object_or_404(SSHCredential, id=credential_id)
    
    if request.method == 'POST':
        try:
            # Get form data
            username = request.POST.get('username')
            password = request.POST.get('password')
            port = request.POST.get('port', 22)
            private_key_path = request.POST.get('private_key_path', '')
            is_active = request.POST.get('is_active') == 'on'
            
            # Update credential
            credential.username = username
            credential.port = port
            credential.private_key_path = private_key_path
            credential.is_active = is_active
            
            # Update password only if provided
            if password:
                credential.set_password(password)
            
            credential.save()
            
            messages.success(request, f'SSH credential updated for {credential.server.name}')
            return redirect('ssh_credentials_list')
            
        except Exception as e:
            messages.error(request, f'Error updating SSH credential: {str(e)}')
    
    context = {
        'title': 'Edit SSH Credential',
        'credential': credential,
        'action': 'edit'
    }
    
    return render(request, 'monitor/ssh_credential_form.html', context)


@login_required
def ssh_credential_delete(request, credential_id):
    """Delete SSH credential"""
    credential = get_object_or_404(SSHCredential, id=credential_id)
    
    if request.method == 'POST':
        server_name = credential.server.name
        credential.delete()
        messages.success(request, f'SSH credential deleted for {server_name}')
        return redirect('ssh_credentials_list')
    
    context = {
        'title': 'Delete SSH Credential',
        'credential': credential
    }
    
    return render(request, 'monitor/ssh_credential_delete.html', context)


@login_required
@require_http_methods(["POST"])
def ssh_credential_test(request, credential_id):
    """Test SSH credential connection"""
    credential = get_object_or_404(SSHCredential, id=credential_id)
    
    try:
        success, message = credential.test_connection()
        
        if success:
            messages.success(request, f'Connection test successful for {credential.server.name}')
        else:
            messages.error(request, f'Connection test failed for {credential.server.name}: {message}')
            
    except Exception as e:
        messages.error(request, f'Error testing connection: {str(e)}')
    
    return redirect('ssh_credentials_list')


@login_required
def metrics_config_list(request):
    """List all server metrics configurations"""
    configs = ServerMetricsConfig.objects.select_related('server').all()
    
    context = {
        'configs': configs,
        'title': 'Server Metrics Configuration'
    }
    
    return render(request, 'monitor/metrics_config_list.html', context)


@login_required
def metrics_config_edit(request, server_id):
    """Edit server metrics configuration"""
    server = get_object_or_404(Server, id=server_id)
    
    # Get or create config
    config, created = ServerMetricsConfig.objects.get_or_create(
        server=server,
        defaults={
            'is_active': True,
            'enable_cpu_monitoring': True,
            'enable_ram_monitoring': True,
            'enable_disk_monitoring': True,
            'enable_ssl_monitoring': True,
        }
    )
    
    if request.method == 'POST':
        try:
            # Update configuration
            config.enable_cpu_monitoring = request.POST.get('enable_cpu_monitoring') == 'on'
            config.enable_ram_monitoring = request.POST.get('enable_ram_monitoring') == 'on'
            config.enable_disk_monitoring = request.POST.get('enable_disk_monitoring') == 'on'
            config.enable_ssl_monitoring = request.POST.get('enable_ssl_monitoring') == 'on'
            
            config.cpu_threshold_warning = float(request.POST.get('cpu_threshold_warning', 80))
            config.cpu_threshold_critical = float(request.POST.get('cpu_threshold_critical', 95))
            config.ram_threshold_warning = float(request.POST.get('ram_threshold_warning', 80))
            config.ram_threshold_critical = float(request.POST.get('ram_threshold_critical', 95))
            config.disk_threshold_warning = float(request.POST.get('disk_threshold_warning', 80))
            config.disk_threshold_critical = float(request.POST.get('disk_threshold_critical', 95))
            config.ssl_warning_days = int(request.POST.get('ssl_warning_days', 30))
            config.ssl_critical_days = int(request.POST.get('ssl_critical_days', 7))
            config.monitoring_interval = int(request.POST.get('monitoring_interval', 300))
            config.is_active = request.POST.get('is_active') == 'on'
            
            config.save()
            
            messages.success(request, f'Metrics configuration updated for {server.name}')
            return redirect('metrics_config_list')
            
        except ValidationError as e:
            messages.error(request, f'Validation error: {str(e)}')
        except Exception as e:
            messages.error(request, f'Error updating configuration: {str(e)}')
    
    context = {
        'title': 'Metrics Configuration',
        'server': server,
        'config': config
    }
    
    return render(request, 'monitor/metrics_config_form.html', context)


@login_required
@csrf_exempt
@require_http_methods(["GET"])
def server_metrics_api(request, server_id):
    """API endpoint to get server metrics with SSH credentials"""
    try:
        server = get_object_or_404(Server, id=server_id)
        
        # Check if server has SSH credentials
        credential = SSHCredential.objects.filter(server=server, is_active=True).first()
        if not credential:
            return JsonResponse({
                'success': False,
                'error': 'No SSH credentials configured for this server'
            }, status=400)
        
        # Check if metrics monitoring is enabled
        config = ServerMetricsConfig.objects.filter(server=server, is_active=True).first()
        if not config:
            return JsonResponse({
                'success': False,
                'error': 'Metrics monitoring not enabled for this server'
            }, status=400)
        
        # Get metrics using the service
        monitor = MetricsMonitorService()
        
        # Update service with server's SSH credentials
        monitor.ssh_credentials[server.ip_address] = {
            'username': credential.username,
            'password': credential.get_password()
        }
        
        metrics_data = monitor.get_comprehensive_metrics(server.ip_address)
        
        if 'error' in metrics_data:
            return JsonResponse({
                'success': False,
                'error': metrics_data['error'],
                'timestamp': metrics_data.get('timestamp')
            }, status=500)
        
        return JsonResponse({
            'success': True,
            'server': {
                'id': server.id,
                'name': server.name,
                'ip_address': server.ip_address
            },
            'metrics': metrics_data['current'],
            'changes': metrics_data['changes'],
            'config': {
                'cpu_threshold_warning': config.cpu_threshold_warning,
                'cpu_threshold_critical': config.cpu_threshold_critical,
                'ram_threshold_warning': config.ram_threshold_warning,
                'ram_threshold_critical': config.ram_threshold_critical,
                'disk_threshold_warning': config.disk_threshold_warning,
                'disk_threshold_critical': config.disk_threshold_critical,
                'ssl_warning_days': config.ssl_warning_days,
                'ssl_critical_days': config.ssl_critical_days
            },
            'timestamp': metrics_data['timestamp'],
            'cached': metrics_data.get('cached', False)
        })
        
    except Exception as e:
        logger.error(f"Error getting server metrics: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def refresh_server_metrics_api(request, server_id):
    """API endpoint to force refresh server metrics"""
    try:
        server = get_object_or_404(Server, id=server_id)
        
        # Clear cache for this server
        from django.core.cache import cache
        cache_key = f'device_metrics_{server.ip_address}'
        cache.delete(cache_key)
        
        # Get fresh metrics
        credential = SSHCredential.objects.filter(server=server, is_active=True).first()
        if not credential:
            return JsonResponse({
                'success': False,
                'error': 'No SSH credentials configured for this server'
            }, status=400)
        
        monitor = MetricsMonitorService()
        monitor.ssh_credentials[server.ip_address] = {
            'username': credential.username,
            'password': credential.get_password()
        }
        
        metrics_data = monitor.get_comprehensive_metrics(server.ip_address)
        
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
        
    except Exception as e:
        logger.error(f"Error refreshing server metrics: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
