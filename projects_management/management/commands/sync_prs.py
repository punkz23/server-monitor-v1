from django.core.management.base import BaseCommand
from projects_management.models import Project
from projects_management.github_service import github_sync_service

class Command(BaseCommand):
    help = 'Synchronize pull requests from GitHub for all projects'

    def add_arguments(self, parser):
        parser.add_argument(
            '--project',
            type=str,
            help='Sync PRs only for a specific project name',
        )

    def handle(self, *args, **options):
        project_name = options.get('project')
        
        if project_name:
            projects = Project.objects.filter(name=project_name)
            if not projects.exists():
                self.stdout.write(self.style.ERROR(f"Project '{project_name}' not found."))
                return
        else:
            projects = Project.objects.all()

        self.stdout.write(f"Syncing PRs for {projects.count()} projects...")

        for project in projects:
            self.stdout.write(f"Syncing {project.name}...")
            success = github_sync_service.sync_pull_requests(project)
            if success:
                self.stdout.write(self.style.SUCCESS(f"  Successfully synced {project.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"  Failed to sync {project.name} (check logs)"))

        self.stdout.write(self.style.SUCCESS("PR synchronization complete."))
