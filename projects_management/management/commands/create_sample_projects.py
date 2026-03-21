from django.core.management.base import BaseCommand
from projects_management.models import Project, Server

class Command(BaseCommand):
    help = 'Create sample projects for testing'

    def handle(self, *args, **options):
        # Clear existing data
        Project.objects.all().delete()
        Server.objects.all().delete()
        
        # Create sample projects
        projects_data = [
            {
                'name': 'new_online_website',
                'repo_url': 'https://github.com/rsdaroy/new_online_website.git',
                'github_token': 'GITHUB_TOKEN_HERE'
            },
            {
                'name': 'new_track_and_trace',
                'repo_url': 'https://github.com/rsdaroy/new_track_and_trace.git',
                'github_token': 'GITHUB_TOKEN_HERE'
            },
            {
                'name': 'management',
                'repo_url': 'https://github.com/rsdaroy/management.git',
                'github_token': 'GITHUB_TOKEN_HERE'
            },
            {
                'name': 'fuelhub',
                'repo_url': 'https://github.com/rsdaroy/fuelhub.git',
                'github_token': 'GITHUB_TOKEN_HERE'
            },
        ]

        created_projects = []
        for proj_data in projects_data:
            project = Project.objects.create(**proj_data)
            created_projects.append(project)
            self.stdout.write(f'Created project: {project.name}')

        # Create sample servers
        servers_data = [
            {
                'hostname': '192.168.254.13',
                'user': 'w4-assistant',
                'password': 'O6G1Amvos0icqGRC',
                'path': '/var/www/new_online_website',
                'project': created_projects[0]
            },
            {
                'hostname': '192.168.254.13',
                'user': 'w4-assistant',
                'password': 'O6G1Amvos0icqGRC',
                'path': '/var/www/new_track_and_trace',
                'project': created_projects[1]
            },
            {
                'hostname': '192.168.254.7',
                'user': 'hp44k6q2-assistant',
                'password': 'Jed9TIYYlwHWl5eu',
                'path': '/var/www/html/management',
                'project': created_projects[2]
            },
            {
                'hostname': '192.168.254.7',
                'user': 'hp44k6q2-assistant',
                'password': 'Jed9TIYYlwHWl5eu',
                'path': '/var/www/html/fuelhub',
                'project': created_projects[3]
            },
        ]

        for server_data in servers_data:
            server = Server.objects.create(**server_data)
            self.stdout.write(f'Created server: {server.hostname} -> {server.path}')

        self.stdout.write(self.style.SUCCESS('Sample projects and servers created successfully!'))
