import requests
import logging
import re
from django.utils import timezone
from .models import Project, PullRequest, PullRequestStatusHistory
from monitor.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

class GitHubSyncService:
    def __init__(self):
        self.notifier = NotificationService()

    def parse_repo_url(self, repo_url):
        """
        Extract owner and repo name from GitHub URL.
        Supports both https://github.com/owner/repo.git and https://github.com/owner/repo
        """
        match = re.search(r'github\.com/([^/]+)/([^/\.]+)', repo_url)
        if match:
            return match.group(1), match.group(2)
        return None, None

    def sync_pull_requests(self, project):
        """
        Fetch pull requests from GitHub and update local database.
        """
        owner, repo = self.parse_repo_url(project.repo_url)
        if not owner or not repo:
            logger.error(f"Could not parse GitHub URL for project {project.name}: {project.repo_url}")
            return False

        url = f"https://api.github.com/repos/{owner}/{repo}/pulls?state=all&per_page=100"
        headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        
        if project.github_token and project.github_token != "GITHUB_TOKEN_HERE":
            headers["Authorization"] = f"token {project.github_token}"

        try:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                logger.error(f"GitHub API error for {project.name}: {response.status_code} - {response.text}")
                return False

            pull_requests_data = response.json()
            
            for pr_data in pull_requests_data:
                github_id = pr_data['id']
                
                # Map GitHub state to local status
                status = 'pending'
                if pr_data.get('merged_at'): # Corrected: use 'merged_at' for merged status
                    status = 'merged'
                elif pr_data['state'] == 'closed':
                    status = 'rejected'
                elif pr_data['state'] == 'open':
                    status = 'pending'
                
                # Convert GitHub timestamps to Django timezone-aware datetime objects
                github_created_at = None
                if pr_data.get('created_at'):
                    github_created_at = timezone.datetime.fromisoformat(pr_data['created_at'].replace('Z', '+00:00'))

                merged_at = None
                if pr_data.get('merged_at'):
                    merged_at = timezone.datetime.fromisoformat(pr_data['merged_at'].replace('Z', '+00:00'))
                
                # Check if it's a new PR or a status change to notify
                existing_pr = PullRequest.objects.filter(github_id=github_id).first()
                
                pr, created = PullRequest.objects.update_or_create(
                    github_id=github_id,
                    defaults={
                        'project': project,
                        'number': pr_data['number'],
                        'title': pr_data['title'],
                        'description': pr_data.get('body') or "",
                        'requester': pr_data['user']['login'],
                        'status': status,
                        'source_branch': pr_data['head']['ref'],
                        'target_branch': pr_data['base']['ref'],
                        'html_url': pr_data['html_url'],
                        'github_created_at': github_created_at,
                        'merged_at': merged_at,
                        'updated_at': timezone.now()
                    }
                )

                if created:
                    self.notifier.send_notification(
                        ['push', 'console', 'telegram'],
                        'all',
                        f"New PR: {project.name}",
                        f"PR #{pr.number}: {pr.title} by {pr.requester}"
                    )
                    # Record initial status
                    PullRequestStatusHistory.objects.create(
                        pull_request=pr,
                        status=pr.status,
                        changed_at=github_created_at or timezone.now() # Use GitHub created_at if available, otherwise now
                    )
                elif existing_pr and existing_pr.status != pr.status:
                    self.notifier.send_notification(
                        ['push', 'console', 'telegram'],
                        'all',
                        f"PR Status Changed: {project.name}",
                        f"PR #{pr.number}: {pr.title} changed from {existing_pr.status} to {pr.status}"
                    )
                    # Record status change
                    PullRequestStatusHistory.objects.create(
                        pull_request=pr,
                        status=pr.status,
                        changed_at=timezone.now() # Use current time for status change
                    )
            
            # Optional: Remove mock PRs if real PRs were found
            if len(pull_requests_data) > 0:
                project.pull_requests.filter(github_id__isnull=True).delete()

            return True

        except Exception as e:
            logger.exception(f"Error syncing PRs for {project.name}: {e}")
            return False

github_sync_service = GitHubSyncService()
