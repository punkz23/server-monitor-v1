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
