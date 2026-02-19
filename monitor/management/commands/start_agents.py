from django.core.management.base import BaseCommand
from django.utils import timezone
import sys
import os

class Command(BaseCommand):
    help = 'Start ServerWatch agents without server restart'

    def add_arguments(self, parser):
        parser.add_argument(
            '--server-id',
            type=int,
            help='Start agent on specific server ID'
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List servers with installed agents'
        )
        parser.add_argument(
            '--status',
            action='store_true',
            help='Check agent status on all servers'
        )

    def handle(self, *args, **options):
        server_id = options.get('server_id')
        list_agents = options.get('list')
        check_status = options.get('status')
        
        # Import the starter
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from start_agents import AgentStarter
        
        starter = AgentStarter()
        
        if list_agents:
            starter.get_servers_with_agents()
            servers_with_agents = starter.get_servers_with_agents()
            self.stdout.write(
                self.style.SUCCESS(f'Found {len(servers_with_agents)} servers with installed agents:')
            )
            
            for i, server_cred in enumerate(servers_with_agents, 1):
                server = server_cred['server']
                self.stdout.write(f'{i}. {server.name} ({server.ip_address})')
                self.stdout.write(f'   Status: {server.agent_status or "unknown"}')
                self.stdout.write(f'   Last Heartbeat: {server.last_agent_heartbeat or "Never"}')
                self.stdout.write('')
                
        elif check_status:
            from monitor.models import Server
            servers = Server.objects.filter(agent_token__isnull=False)
            
            self.stdout.write(
                self.style.SUCCESS('Agent Status for All Servers:')
            )
            self.stdout.write('-' * 50)
            
            for server in servers:
                status_icon = "🟢" if server.agent_status == 'online' else "🔴" if server.agent_status == 'offline' else "⚪"
                self.stdout.write(f'{status_icon} {server.name} ({server.ip_address}): {server.agent_status or "unknown"}')
                if server.last_agent_heartbeat:
                    self.stdout.write(f'   Last heartbeat: {server.last_agent_heartbeat.strftime("%Y-%m-%d %H:%M:%S")}')
                else:
                    self.stdout.write('   Last heartbeat: Never')
                    
        elif server_id:
            from monitor.models import Server
            from monitor.models_ssh_credentials import SSHCredential
            
            try:
                server = Server.objects.get(id=server_id)
                cred = server.ssh_credential
                
                if not cred or not cred.is_active or not server.agent_token:
                    self.stdout.write(
                        self.style.ERROR(f'Server {server.name} has no agent installed')
                    )
                    return
                
                self.stdout.write(
                    self.style.SUCCESS(f'Starting agent on {server.name}...')
                )
                
                starter.start_agent_on_server(server, cred)
                
                if starter.started_count > 0:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Agent started successfully on {server.name}')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Failed to start agent on {server.name}')
                    )
                    
            except Server.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Server with ID {server_id} not found')
                )
        else:
            self.stdout.write(
                self.style.SUCCESS('Starting all agents...')
            )
            starter.start_all_agents()
            
            if starter.started_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ {starter.started_count} agents started successfully')
                )
            
            if starter.failed_count > 0:
                self.stdout.write(
                    self.style.ERROR(f'❌ {starter.failed_count} agents failed to start')
                )
