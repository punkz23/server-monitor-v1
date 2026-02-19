
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.models import Server
from monitor.models_ssh_credentials import SSHCredential

def get_credentials():
    credentials_list = []
    try:
        servers = Server.objects.filter(enabled=True)
        for server in servers:
            try:
                cred = SSHCredential.objects.get(server=server)
                credentials_list.append({
                    'server_name': server.name,
                    'ip_address': server.ip_address,
                    'username': cred.username,
                    'password': cred.get_password(), # Assuming get_password() is safe for direct use here
                    'port': cred.port
                })
            except SSHCredential.DoesNotExist:
                print(f"No SSH credentials found for server: {server.name} ({server.ip_address})", file=sys.stderr)
            except Exception as e:
                print(f"Error fetching credentials for {server.name}: {e}", file=sys.stderr)
    except Exception as e:
        print(f"Error accessing Server models: {e}", file=sys.stderr)
    
    return credentials_list

if __name__ == "__main__":
    creds = get_credentials()
    if creds:
        for c in creds:
            print(f"Server: {c['server_name']} ({c['ip_address']})")
            print(f"  Username: {c['username']}")
            print(f"  Password: {c['password']}")
            print(f"  Port: {c['port']}")
            print("-" * 30)
    else:
        print("No enabled servers with SSH credentials found.")
