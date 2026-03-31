import logging
from django.core.management.base import BaseCommand
from monitor.models import Server

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Cleans up problematic directories from monitored_directories for all servers.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting cleanup of monitored directories...'))

        PROBLEM_DIRECTORIES = ['/home/user/logs', '/var/www/html']

        servers_updated = 0

        for server in Server.objects.all():
            if server.monitored_directories:
                # Split the string into a list, remove problematic entries, and join back
                directories = [d.strip() for d in server.monitored_directories.split(',') if d.strip()]

                initial_directories_set = set(directories)

                for problem_dir in PROBLEM_DIRECTORIES:
                    if problem_dir in directories:
                        self.stdout.write(f"Found '{problem_dir}' in server '{server.name}' ({server.ip_address}). Removing...")
                        directories.remove(problem_dir)

                if set(directories) != initial_directories_set:
                    server.monitored_directories = ','.join(directories)
                    server.save(update_fields=['monitored_directories'])
                    servers_updated += 1
                else:
                    self.stdout.write(f"No problematic directories found in server '{server.name}' ({server.ip_address}). Skipping.")
            else:
                self.stdout.write(f"No monitored directories for server '{server.name}' ({server.ip_address}). Skipping.")

        if servers_updated > 0:
            self.stdout.write(self.style.SUCCESS(f'Successfully updated {servers_updated} server(s).'))
        else:
            self.stdout.write(self.style.SUCCESS('No servers needed an update for monitored directories.'))
