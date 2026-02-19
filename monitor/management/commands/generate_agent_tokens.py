from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string
from monitor.models import Server
import secrets

class Command(BaseCommand):
    help = 'Generate agent tokens for servers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--server-id',
            type=int,
            help='Generate token for specific server ID'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Generate tokens for all servers without tokens'
        )
        parser.add_argument(
            '--regenerate',
            action='store_true',
            help='Regenerate existing tokens'
        )
        parser.add_argument(
            '--length',
            type=int,
            default=32,
            help='Token length (default: 32)'
        )

    def handle(self, *args, **options):
        server_id = options.get('server_id')
        generate_all = options.get('all')
        regenerate = options.get('regenerate')
        token_length = options.get('length')

        if server_id:
            # Generate token for specific server
            try:
                server = Server.objects.get(id=server_id)
                self.generate_token(server, regenerate, token_length)
            except Server.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Server with ID {server_id} not found')
                )
        elif generate_all:
            # Generate tokens for all servers
            servers = Server.objects.all()
            if not regenerate:
                servers = servers.filter(agent_token__isnull=True)
            
            count = 0
            for server in servers:
                self.generate_token(server, regenerate, token_length)
                count += 1
            
            self.stdout.write(
                self.style.SUCCESS(f'Generated tokens for {count} servers')
            )
        else:
            self.stdout.write(
                self.style.ERROR('Please specify --server-id or --all')
            )

    def generate_token(self, server, regenerate=False, length=32):
        """Generate agent token for server"""
        if server.agent_token and not regenerate:
            self.stdout.write(
                self.style.WARNING(
                    f'Server {server.name} already has a token. '
                    f'Use --regenerate to overwrite.'
                )
            )
            return

        # Generate secure token
        token = secrets.token_urlsafe(length)
        
        # Update server
        server.agent_token = token
        server.save(update_fields=['agent_token', 'updated_at'])
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Generated token for {server.name} ({server.ip_address}): {token}'
            )
        )
