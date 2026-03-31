import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.models import Server
from monitor.models_ssh_credentials import SSHCredential

failed_ips = ['192.168.253.31', '192.168.253.15', '192.168.253.7', '192.168.254.19', '192.168.254.13', '192.168.254.12', '192.168.254.10', '192.168.254.7']

config = {
    "agent_version": "1.1.0-light",
    "install_path": "serverwatch-agent",
    "service_name": "serverwatch-agent",
    "port": 8001,
    "log_level": "INFO",
    "metrics_interval": 30,
    "heartbeat_interval": 60,
    "ssh_port": 22,
    "ssh_timeout": 60,  # Increased timeout
    "servers": []
}

SERVER_URL = "http://192.168.253.31:8001"

for ip in failed_ips:
    try:
        s = Server.objects.get(ip_address=ip)
        cred = s.ssh_credential
        server_info = {
            "hostname": s.ip_address,
            "username": cred.username,
            "password": cred.get_password(),
            "server_url": SERVER_URL,
            "agent_token": s.agent_token or f"agent-{s.id}",
            "start_service": True
        }
        config["servers"].append(server_info)
    except Exception:
        continue

with open('agent_config_retry.json', 'w') as f:
    json.dump(config, f, indent=2)

print(f"Generated retry configuration for {len(config['servers'])} servers.")
