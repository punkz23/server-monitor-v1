from rest_framework import serializers
from .models import Project, Server, PullRequest, PullRequestStatusHistory

class ServerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Server
        fields = ['id', 'hostname', 'user', 'path', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class PullRequestStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PullRequestStatusHistory
        fields = ['status', 'changed_at']

class PullRequestSerializer(serializers.ModelSerializer):
    status_history = PullRequestStatusHistorySerializer(many=True, read_only=True)

    class Meta:
        model = PullRequest
        fields = [
            'id', 'title', 'description', 'requester', 'status', 
            'source_branch', 'target_branch', 'html_url',
            'github_created_at', 'merged_at',
            'updated_at',
            'status_history'
        ]
        read_only_fields = ['created_at', 'updated_at']

class ProjectSerializer(serializers.ModelSerializer):
    servers = ServerSerializer(many=True, read_only=True)
    pull_requests = PullRequestSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'name', 'repo_url', 'github_token', 'servers', 'pull_requests', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'github_token']

class GitPullSerializer(serializers.Serializer):
    server_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="List of server IDs on which to perform the Git pull."
    )

class CustomCommandSerializer(serializers.Serializer):
    server_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="List of server IDs on which to execute the custom command."
    )
    command = serializers.CharField(
        max_length=1000, # Increased max_length to accommodate longer commands
        allow_blank=False,
        help_text="The custom command string to execute on the remote server(s)."
    )
