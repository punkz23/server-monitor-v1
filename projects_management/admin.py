from django.contrib import admin
from .models import Project, Server

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'repo_url', 'created_at', 'updated_at')
    search_fields = ('name', 'repo_url')
    list_filter = ('created_at', 'updated_at')

@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = ('project', 'hostname', 'user', 'path', 'created_at', 'updated_at')
    search_fields = ('project__name', 'hostname', 'user', 'path')
    list_filter = ('project', 'created_at', 'updated_at')
