from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from .models import Project, Server
from .serializers import ProjectSerializer, ServerSerializer, GitPullSerializer, CustomCommandSerializer
from .ssh_service import ssh_service
import logging

logger = logging.getLogger(__name__)

class ProjectListView(APIView):
    permission_classes = [AllowAny]  # Allow unauthenticated access to projects list
    
    def get(self, request):
        projects = Project.objects.all()
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data)

class ProjectDetailView(APIView):
    def get(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        serializer = ProjectSerializer(project)
        return Response(serializer.data)

class GitPullView(APIView):
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        serializer = GitPullSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        server_ids = serializer.validated_data['server_ids']

        selected_servers = project.servers.filter(id__in=server_ids)
        if not selected_servers.exists():
            return Response(
                {"detail": "No valid servers found for the given project and server IDs."},
                status=status.HTTP_400_BAD_REQUEST
            )

        results = []
        for server in selected_servers:
            # Construct the git pull command
            if project.github_token:
                # Use the token for authenticated git operations
                git_command = f"git pull https://oauth2:{project.github_token}@github.com/{project.repo_url.split('github.com/')[-1]}"
            else:
                # Assume public repo or SSH key based access if no token
                git_command = f"git pull {project.repo_url}"
            
            logger.info(f"Initiating git pull for project '{project.name}' on {server.hostname} with command: {git_command}")
            
            result = ssh_service.execute_command(server, git_command)
            
            results.append({
                "server_id": server.id,
                "hostname": server.hostname,
                "stdout": result.get("stdout"),
                "stderr": result.get("stderr"),
                "exit_code": result.get("exit_code"),
                "success": result.get("exit_code") == 0
            })
        
        # Check if all commands failed
        if all(not res['success'] for res in results):
            return Response(results, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(results, status=status.HTTP_200_OK)

class CustomCommandView(APIView):
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        serializer = CustomCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        server_ids = serializer.validated_data['server_ids']
        command = serializer.validated_data['command']

        selected_servers = project.servers.filter(id__in=server_ids)
        if not selected_servers.exists():
            return Response(
                {"detail": "No valid servers found for the given project and server IDs."},
                status=status.HTTP_400_BAD_REQUEST
            )

        results = []
        for server in selected_servers:
            logger.info(f"Executing custom command '{command}' for project '{project.name}' on {server.hostname}")
            
            result = ssh_service.execute_command(server, command)
            
            results.append({
                "server_id": server.id,
                "hostname": server.hostname,
                "stdout": result.get("stdout"),
                "stderr": result.get("stderr"),
                "exit_code": result.get("exit_code"),
                "success": result.get("exit_code") == 0
            })

        # Check if all commands failed
        if all(not res['success'] for res in results):
            return Response(results, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        return Response(results, status=status.HTTP_200_OK)
