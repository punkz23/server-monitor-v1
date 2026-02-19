from django.core.management.base import BaseCommand
from django.utils import timezone
import subprocess
import sys
import os

class Command(BaseCommand):
    help = 'Deploy agents to all servers with SSH credentials'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deployed without actually deploying'
        )
        parser.add_argument(
            '--list',
            action='store_true', 
            help='List servers with SSH credentials'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force redeployment even if agent is already running'
        )

    def handle(self, *args, **options):
        # Import the auto deployer
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        try:
            from auto_deploy_agents import AutomatedAgentDeployer
            from monitor.models_ssh_credentials import SSHCredential
            
            deployer = AutomatedAgentDeployer()
            
            if options['list']:
                servers_with_creds = deployer.get_servers_with_credentials()
                self.stdout.write(
                    self.style.SUCCESS(f'Found {len(servers_with_creds)} servers with SSH credentials:')
                )
                
                for i, server_cred in enumerate(servers_with_creds, 1):
                    server = server_cred['server']
                    cred = server_cred['credential']
                    self.stdout.write(f'{i}. {server.name} ({server.ip_address})')
                    self.stdout.write(f'   User: {cred.username}')
                    self.stdout.write(f'   Port: {cred.port}')
                    self.stdout.write(f'   Auth: {"Key" if cred.private_key_path else "Password"}')
                    self.stdout.write(f'   Agent Status: {server.agent_status or "Unknown"}')
                    self.stdout.write('')
                    
            elif options['dry_run']:
                servers_with_creds = deployer.get_servers_with_credentials()
                self.stdout.write(
                    self.style.WARNING(f'DRY RUN - Would deploy to {len(servers_with_creds)} servers:')
                )
                
                for server_cred in servers_with_creds:
                    server = server_cred['server']
                    self.stdout.write(f'   - {server.name} ({server.ip_address})')
                    
            else:
                self.stdout.write(
                    self.style.SUCCESS('Starting automated agent deployment...')
                )
                deployer.deploy_to_all()
                
        except ImportError as e:
            self.stdout.write(
                self.style.ERROR(f'Error importing deployer: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Deployment failed: {e}')
            )
