import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.models import Server as MonitorServer
from projects_management.models import Project, Server as ProjectServer

GITHUB_TOKEN = "GITHUB_TOKEN_HERE"

def add_server_and_projects(name, ip, location, username, password, projects_data):
    # 1. Add to MonitorServer if doesn't exist
    monitor_server, created = MonitorServer.objects.get_or_create(
        ip_address=ip,
        defaults={
            'name': name,
            'server_type': 'WEB',
            'tags': location,
            'enabled': True
        }
    )
    if not created:
        print(f"Server {name} ({ip}) already exists in monitor.")
    else:
        print(f"Created server {name} ({ip}) in monitor.")

    # 2. Add Projects and Link them to this server
    for proj_data in projects_data:
        directory = proj_data['directory']
        git_url = proj_data['git_url']
        
        # Determine project name from git url or use a reasonable name
        # e.g., https://github.com/rsdaroy/new_online_website.git -> new_online_website
        proj_name = git_url.split('/')[-1].replace('.git', '')
        
        project, p_created = Project.objects.get_or_create(
            name=proj_name,
            defaults={
                'repo_url': git_url,
                'github_token': GITHUB_TOKEN
            }
        )
        if p_created:
            print(f"  Created Project: {proj_name}")
        
        # Link project to this server path
        ps, ps_created = ProjectServer.objects.get_or_create(
            project=project,
            hostname=ip,
            path=directory,
            defaults={
                'user': username,
                'password': password
            }
        )
        if ps_created:
            print(f"    Linked {proj_name} to {ip} at {directory}")
        else:
            print(f"    Link for {proj_name} at {ip}:{directory} already exists.")

def main():
    data = [
        {
            'name': 'onlinebooking',
            'ip': '192.168.254.13',
            'location': 'Manila',
            'username': 'w4-assistant',
            'password': 'O6G1Amvos0icqGRC',
            'projects': [
                {'directory': '/var/www/new_online_website', 'git_url': 'https://github.com/rsdaroy/new_online_website.git'},
                {'directory': '/var/www/new_track_and_trace', 'git_url': 'https://github.com/rsdaroy/new_track_and_trace.git'},
                {'directory': '/var/www/new_supplier', 'git_url': 'https://github.com/rsdaroy/new_supplier.git'},
                {'directory': '/var/www/career.dailyoverland', 'git_url': 'https://github.com/rsdaroy/career.dailyoverland.git'},
            ]
        },
        {
            'name': 'server-hp4k6q2',
            'ip': '192.168.254.7',
            'location': 'Manila',
            'username': 'hp44k6q2-assistant',
            'password': 'Jed9TIYYlwHWl5eu',
            'projects': [
                {'directory': '/var/www/html/management', 'git_url': 'https://github.com/rsdaroy/management.git'},
                {'directory': '/var/www/html/doffsystem', 'git_url': 'https://github.com/rsdaroy/doffsystem.git'},
                {'directory': '/var/www/html/fuelhub', 'git_url': 'https://github.com/rsdaroy/fuelhub.git'},
            ]
        },
        {
            'name': 'webserver3',
            'ip': '192.168.254.50',
            'location': 'Manila',
            'username': 'ws3-assistant',
            'password': '6c$7TpzjzYpTpbDp',
            'projects': [
                {'directory': '/var/www/new_employee', 'git_url': 'https://github.com/rsdaroy/new_employee.git'},
                {'directory': '/var/www/new_doff', 'git_url': 'https://github.com/rsdaroy/new_doff.git'},
                {'directory': '/var/www/doff_dtr', 'git_url': 'https://github.com/rsdaroy/doff_dtr.git'},
                {'directory': '/var/www/api', 'git_url': 'https://github.com/rsdaroy/api.git'},
                {'directory': '/var/www/digital_id', 'git_url': 'https://github.com/rsdaroy/digital_id.git'},
            ]
        },
        {
            'name': 'ho-w1',
            'ip': '192.168.253.7',
            'location': 'Head Office - Daraga',
            'username': 'ho-w1-assistant',
            'password': 'PB7hS5jNEhLxvjZN',
            'projects': [
                {'directory': '/var/www/html/management', 'git_url': 'https://github.com/rsdaroy/management.git'},
                {'directory': '/var/www/html/doffsystem', 'git_url': 'https://github.com/rsdaroy/doffsystem.git'},
                {'directory': '/var/www/html/fuelhub', 'git_url': 'https://github.com/rsdaroy/fuelhub.git'},
            ]
        },
        {
            'name': 'w1',
            'ip': '192.168.253.15',
            'location': 'Head Office - Daraga',
            'username': 'w1-assistant',
            'password': 'hIkLM#X5x1sjwIrM',
            'projects': [
                {'directory': '/var/www/new_employee', 'git_url': 'https://github.com/rsdaroy/new_employee.git'},
                {'directory': '/var/www/new_doff', 'git_url': 'https://github.com/rsdaroy/new_doff.git'},
                {'directory': '/var/www/doff_dtr', 'git_url': 'https://github.com/rsdaroy/doff_dtr.git'},
                {'directory': '/var/www/new_online_website', 'git_url': 'https://github.com/rsdaroy/new_online_website.git'},
            ]
        },
    ]

    for item in data:
        add_server_and_projects(
            item['name'], 
            item['ip'], 
            item['location'], 
            item['username'], 
            item['password'], 
            item['projects']
        )

if __name__ == '__main__':
    main()
