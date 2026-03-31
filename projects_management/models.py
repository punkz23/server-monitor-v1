from django.db import models
from .fields import EncryptedCharField

class Project(models.Model):
    name = models.CharField(max_length=255, unique=True)
    repo_url = models.URLField(max_length=500)
    github_token = EncryptedCharField(max_length=500, blank=True, null=True) # Securely store GitHub token
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Server(models.Model):
    project = models.ForeignKey(Project, related_name='servers', on_delete=models.CASCADE)
    hostname = models.CharField(max_length=255)
    user = models.CharField(max_length=255)
    password = EncryptedCharField(max_length=500) # Securely store SSH password
    path = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('project', 'hostname', 'path') # A server path unique to a project
        ordering = ['hostname']

    def __str__(self):
        return f"{self.user}@{self.hostname}:{self.path} ({self.project.name})"

class PullRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('merged', 'Merged'),
        ('rejected', 'Rejected'),
    ]

    project = models.ForeignKey(Project, related_name='pull_requests', on_delete=models.CASCADE)
    github_id = models.BigIntegerField(unique=True, null=True, blank=True)
    number = models.IntegerField(null=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    requester = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    source_branch = models.CharField(max_length=255, blank=True, null=True)
    target_branch = models.CharField(max_length=255, blank=True, null=True)
    html_url = models.URLField(max_length=500, blank=True, null=True)
    github_created_at = models.DateTimeField(null=True, blank=True)
    merged_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"PR #{self.id}: {self.title} ({self.project.name})"

class PullRequestStatusHistory(models.Model):
    pull_request = models.ForeignKey(PullRequest, related_name='status_history', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=PullRequest.STATUS_CHOICES)
    changed_at = models.DateTimeField()
    github_event_id = models.BigIntegerField(null=True, blank=True) # Optional: if we want to link to a specific GitHub event

    class Meta:
        ordering = ['changed_at']
        verbose_name_plural = "Pull Request Status Histories"

    def __str__(self):
        return f"PR #{self.pull_request.number} - {self.status} at {self.changed_at.isoformat()}"
