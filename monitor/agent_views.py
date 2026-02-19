from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Server
from .models_metrics import ServerMetrics
import json
import logging

logger = logging.getLogger(__name__)

def get_server_from_request(request, data):
    """Helper to find server from request token or data"""
    # 1. Try to get token from Authorization header
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        server = Server.objects.filter(agent_token=token).first()
        if server:
            return server

    # 2. Fallback to server_id in data
    server_id = data.get('server_id')
    if server_id:
        # Try exact match on token if it was passed in body
        server = Server.objects.filter(agent_token=server_id).first()
        if server:
            return server
            
        # Try hostname/IP matching
        hostname = server_id.split('-')[0] if '-' in server_id else server_id
        server = Server.objects.filter(
            Q(name__icontains=hostname) | 
            Q(ip_address__icontains=hostname)
        ).first()
        return server
        
    return None

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def agent_heartbeat(request):
    """
    Receive heartbeat from agent
    """
    try:
        data = json.loads(request.body)
        server = get_server_from_request(request, data)
        
        if not server:
            logger.warning(f"Server not found for heartbeat: {data.get('server_id')}")
            return JsonResponse(
                {'error': 'Server not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        agent_status = data.get('status', 'online')
        agent_version = data.get('agent_version')
        
        # Update server agent status
        server.last_agent_heartbeat = timezone.now()
        server.agent_status = agent_status
        server.agent_version = agent_version
        
        # If agent is online, consider the server UP
        if agent_status == 'online':
            server.last_status = 'UP'
            server.last_checked = timezone.now()
            
        server.save(update_fields=['last_agent_heartbeat', 'agent_status', 'agent_version', 'last_status', 'last_checked', 'updated_at'])
        
        logger.info(f"Heartbeat received from {server.name} ({server.ip_address})")
        
        return JsonResponse({
            'status': 'success',
            'server_id': server.id,
            'timestamp': timezone.now().isoformat()
        })
        
    except json.JSONDecodeError:
        return JsonResponse(
            {'error': 'Invalid JSON'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Error processing heartbeat: {e}")
        return JsonResponse(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def agent_metrics(request):
    """
    Receive metrics from agent
    """
    try:
        data = json.loads(request.body)
        server = get_server_from_request(request, data)
        
        if not server:
            logger.warning(f"Server not found for metrics: {data.get('server_id')}")
            return JsonResponse(
                {'error': 'Server not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Extract metrics
        cpu_data = data.get('cpu', {})
        memory_data = data.get('memory', {})
        disk_data = data.get('disk', {})
        network_data = data.get('network', {})
        system_data = data.get('system', {})
        
        # Update server with latest metrics
        server.last_cpu_percent = cpu_data.get('percent')
        server.last_ram_percent = memory_data.get('percent')
        server.last_load_1 = cpu_data.get('load_1m')
        server.last_uptime_seconds = system_data.get('uptime_seconds')
        server.last_agent_metrics = timezone.now()
        server.last_status = 'UP'  # Agent is sending metrics, so server is UP
        server.last_checked = timezone.now() # Update last_checked for dashboard consistency
        
        # Update disk usage percentage
        if disk_data.get('percent') is not None:
            server.last_disk_percent = disk_data.get('percent')
        elif disk_data.get('total') and disk_data.get('used'):
            server.last_disk_percent = (disk_data['used'] / disk_data['total']) * 100
        
        server.save(update_fields=[
            'last_cpu_percent', 'last_ram_percent', 'last_load_1',
            'last_uptime_seconds', 'last_disk_percent', 'last_agent_metrics',
            'updated_at'
        ])
        
        # Broadcast metrics update
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                "status",
                {
                    "type": "server.metrics",
                    "server": {
                        "id": server.id,
                        "last_cpu_percent": server.last_cpu_percent,
                        "last_ram_percent": server.last_ram_percent,
                        "last_disk_percent": server.last_disk_percent,
                        "last_load_1": server.last_load_1,
                        "last_uptime_seconds": server.last_uptime_seconds,
                        "last_agent_metrics": server.last_agent_metrics.isoformat() if server.last_agent_metrics else None,
                    }
                }
            )
        
        # Store detailed metrics in database
        try:
            ServerMetrics.objects.create(
                server=server,
                timestamp=timezone.now(),
                cpu_percent=cpu_data.get('percent'),
                cpu_count=cpu_data.get('count'),
                load_1m=cpu_data.get('load_1m'),
                load_5m=cpu_data.get('load_5m'),
                load_15m=cpu_data.get('load_15m'),
                memory_total=memory_data.get('total'),
                memory_used=memory_data.get('used'),
                memory_percent=memory_data.get('percent'),
                disk_total=disk_data.get('total'),
                disk_used=disk_data.get('used'),
                disk_percent=server.last_disk_percent,
                network_bytes_sent=network_data.get('bytes_sent'),
                network_bytes_recv=network_data.get('bytes_recv'),
                network_packets_sent=network_data.get('packets_sent'),
                network_packets_recv=network_data.get('packets_recv'),
                uptime_seconds=system_data.get('uptime_seconds'),
                process_count=system_data.get('process_count'),
                hostname=system_data.get('hostname'),
                agent_server_id=data.get('server_id', f"agent-{server.id}"),
                directory_metrics=data.get('directory_metrics')
            )
        except Exception as e:
            logger.error(f"Error storing metrics: {e}")
        
        logger.info(f"Metrics received from {server.name} ({server.ip_address})")
        
        return JsonResponse({
            'status': 'success',
            'server_id': server.id,
            'timestamp': timezone.now().isoformat()
        })
        
    except json.JSONDecodeError:
        return JsonResponse(
            {'error': 'Invalid JSON'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Error processing metrics: {e}")
        return JsonResponse(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def agent_status(request):
    """
    Get status of all agents
    """
    servers = Server.objects.all()
    
    agent_status = []
    now = timezone.now()
    
    for server in servers:
        status_info = {
            'id': server.id,
            'name': server.name,
            'ip_address': server.ip_address,
            'agent_status': server.agent_status or 'unknown',
            'agent_version': server.agent_version,
            'last_heartbeat': server.last_agent_heartbeat,
            'last_metrics': server.last_agent_metrics,
            'is_online': False
        }
        
        # Check if agent is online (heartbeat within 5 minutes for more lenient check)
        if server.last_agent_heartbeat:
            time_diff = now - server.last_agent_heartbeat
            status_info['is_online'] = time_diff.total_seconds() < 300
            status_info['seconds_since_heartbeat'] = int(time_diff.total_seconds())
        else:
            # Check if agent is online based on agent_status field
            status_info['is_online'] = server.agent_status == 'online'
            status_info['seconds_since_heartbeat'] = None
        
        agent_status.append(status_info)
    
    return Response({
        'agents': agent_status,
        'total_servers': len(agent_status),
        'online_agents': len([s for s in agent_status if s['is_online']]),
        'timestamp': now.isoformat()
    })

@api_view(['POST'])
def deploy_agent(request, server_id):
    """
    Trigger agent deployment to a specific server
    """
    try:
        server = Server.objects.get(id=server_id)
        
        # Get deployment configuration
        config = request.data
        
        # Here you would integrate with your deployment system
        # For now, just return success
        
        return Response({
            'status': 'success',
            'message': f'Agent deployment initiated for {server.name}',
            'server_id': server.id
        })
        
    except Server.DoesNotExist:
        return Response(
            {'error': 'Server not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error deploying agent: {e}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
