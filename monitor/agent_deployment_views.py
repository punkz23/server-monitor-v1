from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from .models import Server
from .models_ssh_credentials import SSHCredential
import subprocess
import json
import threading
import time

@login_required
def agent_deployment_dashboard(request):
    """Agent deployment dashboard"""
    # Get servers with SSH credentials
    servers_with_creds = []
    
    for server in Server.objects.filter(enabled=True):
        try:
            cred = server.ssh_credential
            if cred and cred.is_active:
                servers_with_creds.append({
                    'server': server,
                    'credential': cred,
                    'has_agent': bool(server.agent_token),
                    'agent_status': server.agent_status or 'unknown',
                    'last_heartbeat': server.last_agent_heartbeat
                })
        except:
            continue
    
    context = {
        'servers_with_creds': servers_with_creds,
        'total_servers': len(servers_with_creds),
        'agents_online': len([s for s in servers_with_creds if s['agent_status'] == 'online']),
        'agents_offline': len([s for s in servers_with_creds if s['agent_status'] == 'offline']),
        'agents_unknown': len([s for s in servers_with_creds if s['agent_status'] == 'unknown'])
    }
    
    return render(request, 'monitor/agent_deployment.html', context)

@login_required
@require_http_methods(["POST"])
def deploy_single_agent(request, server_id):
    """Deploy agent to a single server"""
    try:
        server = Server.objects.get(id=server_id)
        cred = server.ssh_credential
        
        if not cred or not cred.is_active:
            messages.error(request, f"No active SSH credentials found for {server.name}")
            return redirect('agent_deployment_dashboard')
        
        # Import deployer
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from auto_deploy_agents import AutomatedAgentDeployer
        
        deployer = AutomatedAgentDeployer()
        
        # Generate token if not exists
        if not server.agent_token:
            server.agent_token = f"agent-{server.id}-{int(time.time())}"
            server.save(update_fields=['agent_token'])
        
        # Deploy to single server
        deployer.deploy_to_server(server, cred)
        
        # Check if deployment was successful
        if deployer.deployed_count > 0:
            messages.success(request, f"✅ Agent deployed successfully to {server.name}")
        else:
            messages.error(request, f"❌ Agent deployment failed for {server.name}")
        
    except Server.DoesNotExist:
        messages.error(request, "Server not found")
    except Exception as e:
        messages.error(request, f"Deployment failed: {str(e)}")
    
    return redirect('agent_deployment_dashboard')

@login_required
@require_http_methods(["POST"])
def deploy_all_agents(request):
    """Deploy agents to all servers with SSH credentials"""
    try:
        # Import deployer
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from auto_deploy_agents import AutomatedAgentDeployer
        
        deployer = AutomatedAgentDeployer()
        
        # Run deployment in background thread
        def background_deploy():
            deployer.deploy_to_all()
        
        thread = threading.Thread(target=background_deploy)
        thread.daemon = True
        thread.start()
        
        messages.success(request, "Agent deployment started for all servers with SSH credentials")
        
    except Exception as e:
        messages.error(request, f"Deployment failed: {str(e)}")
    
    return redirect('agent_deployment_dashboard')

@api_view(['GET'])
@permission_classes([IsAdminUser])
def agent_deployment_status(request):
    """Get deployment status via API"""
    servers_with_creds = []
    
    for server in Server.objects.filter(enabled=True):
        try:
            cred = server.ssh_credential
            if cred and cred.is_active:
                servers_with_creds.append({
                    'id': server.id,
                    'name': server.name,
                    'ip_address': server.ip_address,
                    'agent_status': server.agent_status or 'unknown',
                    'agent_version': server.agent_version,
                    'last_heartbeat': server.last_agent_heartbeat.isoformat() if server.last_agent_heartbeat else None,
                    'last_metrics': server.last_agent_metrics.isoformat() if server.last_agent_metrics else None,
                    'has_agent': bool(server.agent_token),
                    'ssh_username': cred.username,
                    'ssh_port': cred.port,
                    'ssh_auth_type': 'Key' if cred.use_key else 'Password'
                })
        except:
            continue
    
    return Response({
        'servers': servers_with_creds,
        'total': len(servers_with_creds),
        'online': len([s for s in servers_with_creds if s['agent_status'] == 'online']),
        'offline': len([s for s in servers_with_creds if s['agent_status'] == 'offline']),
        'unknown': len([s for s in servers_with_creds if s['agent_status'] == 'unknown']),
        'timestamp': timezone.now().isoformat()
    })

@login_required
@require_http_methods(["POST"])
def restart_agent(request, server_id):
    """Restart agent on a specific server"""
    try:
        server = Server.objects.get(id=server_id)
        cred = server.ssh_credential
        
        if not cred or not cred.is_active:
            messages.error(request, f"No active SSH credentials found for {server.name}")
            return redirect('agent_deployment_dashboard')
        
        # Import deployer for SSH operations
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from auto_deploy_agents import AutomatedAgentDeployer
        
        deployer = AutomatedAgentDeployer()
        
        # Connect and restart service
        try:
            import paramiko
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect using SSH credentials
            if cred.private_key_path:
                key = paramiko.RSAKey.from_private_key_file(cred.private_key_path)
                ssh.connect(
                    server.ip_address, 
                    username=cred.username,
                    pkey=key,
                    port=cred.port,
                    timeout=30
                )
            else:
                ssh.connect(
                    server.ip_address,
                    username=cred.username,
                    password=cred.get_password(),
                    port=cred.port,
                    timeout=30
                )
            
            # Restart agent service
            stdin, stdout, stderr = ssh.exec_command("sudo systemctl restart serverwatch-agent")
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0:
                messages.success(request, f"✅ Agent restarted successfully on {server.name}")
            else:
                error = stderr.read().decode()
                messages.error(request, f"❌ Failed to restart agent on {server.name}: {error}")
            
            ssh.close()
            
        except Exception as e:
            messages.error(request, f"❌ Error restarting agent on {server.name}: {str(e)}")
        
    except Server.DoesNotExist:
        messages.error(request, "Server not found")
    except Exception as e:
        messages.error(request, f"Operation failed: {str(e)}")
    
    return redirect('agent_deployment_dashboard')

@login_required
@require_http_methods(["POST"])
def uninstall_agent(request, server_id):
    """Uninstall agent from a specific server"""
    if request.method == "POST":
        confirm = request.POST.get('confirm')
        if confirm != f"UNINSTALL-{server_id}":
            messages.error(request, "Invalid confirmation. Please check the server name and try again.")
            return redirect('agent_deployment_dashboard')
    
    try:
        server = Server.objects.get(id=server_id)
        cred = server.ssh_credential
        
        if not cred or not cred.is_active:
            messages.error(request, f"No active SSH credentials found for {server.name}")
            return redirect('agent_deployment_dashboard')
        
        # Import deployer for SSH operations
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from auto_deploy_agents import AutomatedAgentDeployer
        
        deployer = AutomatedAgentDeployer()
        
        # Connect and uninstall service
        try:
            import paramiko
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect using SSH credentials
            if cred.private_key_path:
                key = paramiko.RSAKey.from_private_key_file(cred.private_key_path)
                ssh.connect(
                    server.ip_address, 
                    username=cred.username,
                    pkey=key,
                    port=cred.port,
                    timeout=30
                )
            else:
                ssh.connect(
                    server.ip_address,
                    username=cred.username,
                    password=cred.get_password(),
                    port=cred.port,
                    timeout=30
                )
            
            # Stop and disable agent service
            stdin, stdout, stderr = ssh.exec_command("sudo systemctl stop serverwatch-agent")
            stdin, stdout, stderr = ssh.exec_command("sudo systemctl disable serverwatch-agent")
            
            # Remove agent files
            stdin, stdout, stderr = ssh.exec_command("sudo rm -rf /opt/serverwatch-agent")
            stdin, stdout, stderr = ssh.exec_command("sudo rm -f /etc/systemd/system/serverwatch-agent.service")
            stdin, stdout, stderr = ssh.exec_command("sudo rm -f /etc/serverwatch-agent/config.json")
            
            # Reload systemd
            stdin, stdout, stderr = ssh.exec_command("sudo systemctl daemon-reload")
            
            # Update server record
            server.agent_status = 'uninstalled'
            server.agent_token = None
            server.save(update_fields=['agent_status', 'agent_token'])
            
            messages.success(request, f"✅ Agent uninstalled successfully from {server.name}")
            
            ssh.close()
            
        except Exception as e:
            messages.error(request, f"❌ Error uninstalling agent from {server.name}: {str(e)}")
        
    except Server.DoesNotExist:
        messages.error(request, "Server not found")
    except Exception as e:
        messages.error(request, f"Operation failed: {str(e)}")
    
    return redirect('agent_deployment_dashboard')

@login_required
def check_agent_status(request, server_id):
    """Check agent status on a specific server"""
    try:
        server = Server.objects.get(id=server_id)
        cred = server.ssh_credential
        
        if not cred or not cred.is_active:
            messages.error(request, f"No active SSH credentials found for {server.name}")
            return redirect('agent_deployment_dashboard')
        
        # Import deployer for SSH operations
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from auto_deploy_agents import AutomatedAgentDeployer
        
        deployer = AutomatedAgentDeployer()
        
        # Connect and check service status
        try:
            import paramiko
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect using SSH credentials
            if cred.private_key_path:
                key = paramiko.RSAKey.from_private_key_file(cred.private_key_path)
                ssh.connect(
                    server.ip_address, 
                    username=cred.username,
                    pkey=key,
                    port=cred.port,
                    timeout=30
                )
            else:
                ssh.connect(
                    server.ip_address,
                    username=cred.username,
                    password=cred.get_password(),
                    port=cred.port,
                    timeout=30
                )
            
            # Check service status
            stdin, stdout, stderr = ssh.exec_command("sudo systemctl is-active serverwatch-agent")
            service_status = stdout.read().decode().strip()
            
            # Check if service is enabled
            stdin, stdout, stderr = ssh.exec_command("sudo systemctl is-enabled serverwatch-agent")
            service_enabled = stdout.read().decode().strip()
            
            # Get recent logs
            stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u serverwatch-agent --no-pager -n 10")
            recent_logs = stdout.read().decode()
            
            status_info = {
                'service_status': service_status,
                'service_enabled': service_enabled,
                'recent_logs': recent_logs.split('\n')[:5]  # Last 5 log lines
            }
            
            ssh.close()
            
            return render(request, 'monitor/agent_status_detail.html', {
                'server': server,
                'status_info': status_info
            })
            
        except Exception as e:
            messages.error(request, f"❌ Error checking agent status on {server.name}: {str(e)}")
            return redirect('agent_deployment_dashboard')
        
    except Server.DoesNotExist:
        messages.error(request, "Server not found")
    except Exception as e:
        messages.error(request, f"Operation failed: {str(e)}")
    
    return redirect('agent_deployment_dashboard')

@api_view(['POST'])
@permission_classes([IsAdminUser])
def generate_agent_tokens(request):
    """Generate tokens for all servers"""
    try:
        from django.core.management import call_command
        
        # Call management command
        call_command('generate_agent_tokens', '--all')
        
        return Response({
            'status': 'success',
            'message': 'Agent tokens generated for all servers'
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=500)
