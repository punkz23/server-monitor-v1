
import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from django.contrib.auth.models import User
from monitor.models import Server
from monitor.models_ssh_credentials import SSHCredential

def create_mock_data():
    print("Creating mock data...")

    # Create a superuser
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin')
        print("Superuser 'admin' created.")
    else:
        print("Superuser 'admin' already exists.")

    # List of servers to create or update with new credentials
    servers_data = [
        {"name": "Dummy", "ip_address": "192.168.253.80", "username": "ic1", "password": "server", "port": 22}, # Dummy server, using generic password
        {"name": "MNL Web Server Main", "ip_address": "192.168.254.7", "username": "hp44k6q2-assistant", "password": "Jed9TIYYlwHWl5eu", "port": 22},
        {"name": "MNL Web Server #2", "ip_address": "192.168.254.10", "username": "w2-assistant", "password": "q84NYr5TbZGi6vJ5", "port": 22},
        {"name": "MNL Web HA", "ip_address": "192.168.254.12", "username": "w3-assistant", "password": "fodD@IW8LXtttbrc", "port": 22},
        {"name": "MNL Online Booking (Main)", "ip_address": "192.168.254.13", "username": "w4-assistant", "password": "O6G1Amvos0icqGRC", "port": 22},
        {"name": "MNL Online Booking (Backup)", "ip_address": "192.168.254.19", "username": "online_backup-assistant", "password": "UeAvfTu8oBG4", "port": 22},
        {"name": "MNL Web Server (New - Laravel)", "ip_address": "192.168.254.50", "username": "ws3-assistant", "password": "6c$7TpzjzYpTpbDp", "port": 22},
        {"name": "HO Web Server Main", "ip_address": "192.168.253.7", "username": "ho-w1-assistant", "password": "PB7hS5jNEhLxvjZN", "port": 22},
        {"name": "HO Web Server (New - Laravel)", "ip_address": "192.168.253.15", "username": "w1-assistant", "password": "hIkLM#X5x1sjwIrM", "port": 22},
        
        # Database servers with new credentials
        {"name": "MNL Main DB", "ip_address": "192.168.254.5", "username": "s1-assistant", "password": "K%HyWy3qjXLbUet0", "port": 22},
        {"name": "MNL Slave #1", "ip_address": "192.168.254.15", "username": "w5-assistant", "password": "u?gd3MeRUD0z", "port": 22},
        {"name": "MNL Slave #2", "ip_address": "192.168.254.17", "username": "db3-assistant", "password": "c%WCloNUVkjX", "port": 22},
        {"name": "HO Main DB", "ip_address": "192.168.253.5", "username": "ho-db1-assistant", "password": "R$UWNhtZi&Ah", "port": 22},
        {"name": "HO Slave", "ip_address": "192.168.253.9", "username": "ho-db2-assistant", "password": "hJ4S*mm5j%zi", "port": 22},
    ]

    for data in servers_data:
        # Generate agent_token in the format expected by the agent (hostname-IP)
        # Assuming server name is often the hostname, and IP is available
        # This will simulate what the agent's get_server_id() method would produce
        hostname = data["name"].lower().replace(' ', '-').replace('(', '').replace(')', '')
        # Special handling for Dummy, HO Slave - these were using a different format before
        if data["name"] == "Dummy":
            agent_id = "ic-1-192-168-253-80" # This is what the agent on the dummy server actually generates
        elif data["name"] == "HO Slave":
            agent_id = "hodbserver-192-168-253-9" # Example, adjust as per actual agent output
        elif data["name"] == "HO Main DB":
            agent_id = "monsoon-bcl-node10-192-168-253-5" # Example, adjust as per actual agent output
        elif data["name"] == "MNL Main DB":
            agent_id = "sycamore-mnl-node0-192-168-254-5" # Example, adjust as per actual agent output
        elif data["name"] == "MNL Slave #1":
            agent_id = "sycamore-mnl-node4-192-168-254-15" # Example, adjust as per actual agent output
        elif data["name"] == "MNL Slave #2":
            agent_id = "sycamore-mnl-node5-192-168-254-17" # Example, adjust as per actual agent output
        elif data["name"] == "MNL Web HA":
            agent_id = "w3-h310m-h-2-0-192-168-254-12" # Example, adjust as per actual agent output
        elif data["name"] == "MNL Online Booking (Main)":
            agent_id = "onlinebooking-192-168-254-13" # Example, adjust as per actual agent output
        elif data["name"] == "MNL Online Booking (Backup)":
            agent_id = "onlinebookingbackup-192-168-254-19" # Example, adjust as per actual agent output
        elif data["name"] == "MNL Web Server (New - Laravel)":
            agent_id = "webserver3-192-168-254-50" # Example, adjust as per actual agent output
        elif data["name"] == "HO Web Server Main":
            agent_id = "ho-w1-192-168-253-7" # Example, adjust as per actual agent output
        elif data["name"] == "HO Web Server (New - Laravel)":
            agent_id = "w1-192-168-253-15" # Example, adjust as per actual agent output
        else:
            agent_id = f"{hostname}-{data['ip_address'].replace('.', '-')}"

        
        server, created = Server.objects.get_or_create(
            name=data["name"],
            defaults={"ip_address": data["ip_address"], "agent_token": agent_id}
        )
        if created:
            print(f"Server '{server.name}' created.")
        else:
            print(f"Server '{server.name}' already exists, updating agent token to {agent_id}.")
            if server.agent_token != agent_id:
                server.agent_token = agent_id
                server.save()
            else:
                print(f"Agent token for '{server.name}' already up to date ({agent_id}).")
        
        # Create or update SSH credentials for the server
        credential, cred_created = SSHCredential.objects.get_or_create(
            server=server,
            defaults={
                "username": data["username"],
                "port": data["port"],
                "is_active": True
            }
        )
        if cred_created:
            credential.set_password(data["password"])
            credential.save()
            print(f"SSH credentials created for '{server.name}'.")
        else:
            # Always update the password in case it changed or was generic
            if credential.username != data["username"] or credential.port != data["port"] or credential.get_password() != data["password"]:
                credential.username = data["username"]
                credential.port = data["port"]
                credential.set_password(data["password"])
                credential.save()
                print(f"SSH credentials updated for '{server.name}'.")
            else:
                print(f"SSH credentials for '{server.name}' already up to date.")
            
    print("Mock data creation complete.")

if __name__ == "__main__":
    create_mock_data()
