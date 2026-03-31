import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.models import Server
from monitor.models_ssh_credentials import SSHCredential

config = {
    "agent_version": "1.1.0-light",
    "install_path": "serverwatch-agent",
    "service_name": "serverwatch-agent",
    "port": 8001,
    "log_level": "INFO",
    "metrics_interval": 30,
    "heartbeat_interval": 60,
    "ssh_port": 22,
    "ssh_timeout": 30,
    "servers": []
}

# The current backend URL
SERVER_URL = "http://192.168.253.31:8001"

servers = Server.objects.all()
for s in servers:
    try:
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
        # Skip servers without credentials
        continue

with open('agent_config_batch.json', 'w') as f:
    json.dump(config, f, indent=2)

print(f"Generated configuration for {len(config['servers'])} servers.")
