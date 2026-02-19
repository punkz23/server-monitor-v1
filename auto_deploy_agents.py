#!/usr/bin/env python3
"""
Automated Agent Deployment using Existing SSH Credentials
Deploys ServerWatch agents to all servers with existing SSH credentials
"""

import os
import sys
import django
import paramiko
import json
import time
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.models import Server
from monitor.models_ssh_credentials import SSHCredential
from django.core.management import call_command
from django.utils import timezone

class AutomatedAgentDeployer:
    def __init__(self):
        self.deployed_count = 0
        self.failed_count = 0
        self.results = []
        
    def get_servers_with_credentials(self):
        """Get all servers with active SSH credentials"""
        servers_with_creds = []
        
        for server in Server.objects.filter(enabled=True):
            try:
                cred = server.ssh_credential
                if cred and cred.is_active:
                    servers_with_creds.append({
                        'server': server,
                        'credential': cred
                    })
            except SSHCredential.DoesNotExist: # Handle case where server has no credential
                continue
                
        return servers_with_creds
    
    def create_agent_files(self):
        """Create agent files for deployment"""
        agent_dir = Path("agent_files")
        agent_dir.mkdir(exist_ok=True)
        
        # Read content from agent/serverwatch_agent.py (the source of truth)
        try:
            with open("agent/serverwatch_agent.py", 'r', encoding='utf-8') as f:
                agent_script_content = f.read()
        except FileNotFoundError:
            raise FileNotFoundError("Error: 'agent/serverwatch_agent.py' not found. Ensure the agent script exists in the 'agent' directory.")
        except Exception as e:
            raise Exception(f"Error reading 'agent/serverwatch_agent.py': {e}")

        # Write the content to agent_files/serverwatch-agent.py
        with open(agent_dir / "serverwatch-agent.py", 'w', newline='\n') as f:
            f.write(agent_script_content)

        # Read and write other agent files from agent_files directory
        for filename in ["requirements.txt", "install.sh", "serverwatch-agent.service"]:
            try:
                with open(Path("agent_files") / filename, 'r', encoding='utf-8') as f_read:
                    content = f_read.read()
                with open(agent_dir / filename, 'w', newline='\n') as f_write:
                    f_write.write(content)
            except FileNotFoundError:
                raise FileNotFoundError(f"Error: Missing agent file in 'agent_files' directory: {filename}")
            except Exception as e:
                raise Exception(f"Error reading/writing {filename}: {e}")
        
        # Make install script executable
        os.chmod(agent_dir / "install.sh", 0o755)
        
        print(f"[SUCCESS] Agent files created in {agent_dir}/")
        return agent_dir
    
    def deploy_to_server(self, server, credential):
        """Deploy agent to a single server using SSH credentials"""
        hostname = server.ip_address
        server_name = server.name
        
        print(f"[DEPLOY] Deploying agent to {server_name} ({hostname})...")
        
        try:
            # Create SSH connection
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect using SSH credentials
            if credential.private_key_path:
                # Use key-based authentication
                key = paramiko.RSAKey.from_private_key_file(credential.private_key_path)
                ssh.connect(
                    hostname, 
                    username=credential.username,
                    pkey=key,
                    port=credential.port,
                    timeout=30
                )
            else:
                # Use password authentication
                ssh.connect(
                    hostname,
                    username=credential.username,
                    password=credential.get_password(),
                    port=credential.port,
                    timeout=30
                )
            
            # Create agent files
            agent_dir = self.create_agent_files()
            
            # Transfer files using SFTP
            sftp = ssh.open_sftp()
            
            # Create remote temp directory
            try:
                ssh.exec_command("rm -rf /tmp/serverwatch-agent")
                ssh.exec_command("mkdir -p /tmp/serverwatch-agent")
            except:
                pass
            
            # Transfer agent files with integrity verification
            for filename in ["serverwatch-agent.py", "requirements.txt", "install.sh"]:
                local_path = agent_dir / filename
                remote_path = f"/tmp/serverwatch-agent/{filename}"
                
                # Get local file hash for verification
                import hashlib
                with open(local_path, 'rb') as f:
                    local_hash = hashlib.sha256(f.read()).hexdigest()
                
                # Transfer file
                sftp.put(str(local_path), remote_path)
                
                # Verify transfer integrity
                with sftp.file(remote_path, 'r') as remote_file:
                    remote_content = remote_file.read()
                    remote_hash = hashlib.sha256(remote_content).hexdigest()
                
                if local_hash != remote_hash:
                    raise Exception(f"File integrity check failed for {filename}")
                
                print(f"[TRANSFER] {filename} - OK")
            
            # Generate agent token if not exists
            if not server.agent_token:
                server.agent_token = f"agent-{server.id}-{int(time.time())}"
                server.save(update_fields=['agent_token'])
            
            # Create configuration
            config = {
                "server_url": f"http://{os.environ.get('SERVER_HOST', '192.168.253.23')}:8001",
                "agent_token": server.agent_token,
                "metrics_interval": 30,
                "heartbeat_interval": 60,
                "log_level": "INFO",
                "monitored_directories": [d.strip() for d in server.monitored_directories.split(',') if d.strip()],
                "directory_timeout": 30 # Default timeout, can be made configurable later
            }
            print(f"DEBUG: Generated server_url for {server_name}: {config['server_url']}")
            
            # Transfer configuration
            config_content = json.dumps(config, indent=2)
            remote_path = "/tmp/serverwatch-agent/config.json"
            
            # Create a file-like object from bytes
            from io import BytesIO
            config_file = BytesIO(config_content.encode())
            sftp.putfo(config_file, remote_path)
            
            # Run installation
            print(f"[INSTALL] Running install script on {server_name}...")
            stdin, stdout, stderr = ssh.exec_command("cd /tmp/serverwatch-agent && bash install.sh", get_pty=True)
            
            # Wait for completion
            exit_status = stdout.channel.recv_exit_status()
            
            # Capture installation output for debugging
            install_output = stdout.read().decode()
            
            if exit_status == 0:
                # Verify installation success
                stdin, stdout, stderr = ssh.exec_command("test -f ~/.serverwatch-agent/serverwatch-agent.py && echo 'installed' || echo 'not_installed'")
                agent_installed = stdout.read().decode().strip()
                
                if agent_installed != 'installed':
                    print(f"[ERROR] Agent installation script finished but file not found on {server_name}")
                    self.results.append({
                        'server': server_name,
                        'status': 'error',
                        'message': 'Installation failed (file not found)'
                    })
                    self.failed_count += 1
                    ssh.close()
                    return

                print(f"[SUCCESS] Agent installed successfully on {server_name}")
                
                # Now start the service in user mode
                stdin, stdout, stderr = ssh.exec_command("systemctl --user start serverwatch-agent", get_pty=True)
                service_exit_status = stdout.channel.recv_exit_status()
                
                if service_exit_status == 0:
                    print(f"[SUCCESS] Agent service started on {server_name}")
                    
                    # Update server record
                    server.agent_status = "online"
                    server.agent_version = "1.0.0"
                    server.last_agent_heartbeat = timezone.now()
                    server.save(update_fields=['agent_status', 'agent_version', 'last_agent_heartbeat'])
                    
                    self.results.append({
                        'server': server_name,
                        'status': 'success',
                        'message': 'Agent deployed and started successfully'
                    })
                    self.deployed_count += 1
                else:
                    service_error = stderr.read().decode()
                    print(f"[WARNING] Agent installed but service failed to start on {server_name}: {service_error}")
                    self.results.append({
                        'server': server_name,
                        'status': 'warning',
                        'message': f'Agent installed but service failed: {service_error}'
                    })
            else:
                error_msg = install_output if install_output else f"Exit status: {exit_status}"
                print(f"[ERROR] Agent installation failed on {server_name}: {error_msg}")
                self.results.append({
                    'server': server_name,
                    'status': 'error',
                    'message': f'Installation failed: {error_msg}'
                })
                self.failed_count += 1
        except Exception as e:
            print(f"[ERROR] Error deploying to {server_name}: {e}")
            self.results.append({
                'server': server_name,
                'status': 'error',
                'message': str(e)
            })
            self.failed_count += 1
    
    def deploy_to_all(self, target_ip=None):
        """Deploy agents to all servers with SSH credentials"""
        servers_with_creds = self.get_servers_with_credentials()
        
        if target_ip:
            servers_with_creds = [sc for sc in servers_with_creds if str(sc['server'].ip_address) == target_ip]
            if not servers_with_creds:
                print(f"[ERROR] No server found with IP: {target_ip}")
                return
        if not servers_with_creds:
            print("[ERROR] No servers with active SSH credentials found")
            return
        
        print(f"[DEPLOY] Starting automated deployment to {len(servers_with_creds)} servers...")
        print("=" * 60)
        
        # Generate tokens for all servers first
        print("[TOKEN] Generating agent tokens...")
        for server_cred in servers_with_creds:
            server = server_cred['server']
            if not server.agent_token:
                server.agent_token = f"agent-{server.id}-{int(time.time())}"
                server.save(update_fields=['agent_token'])
        
        print(f"[SUCCESS] Generated tokens for {len(servers_with_creds)} servers")
        print()
        
        # Deploy to each server
        for i, server_cred in enumerate(servers_with_creds, 1):
            server = server_cred['server']
            credential = server_cred['credential']
            
            print(f"[{i}/{len(servers_with_creds)}] ", end="")
            self.deploy_to_server(server, credential)
            
            # Small delay between deployments
            time.sleep(2)
        
        self.print_summary()
    
    def print_summary(self):
        """Print deployment summary"""
        print("\n" + "=" * 60)
        print("[SUMMARY] DEPLOYMENT SUMMARY")
        print("=" * 60)
        
        print(f"[SUCCESS] Successfully deployed: {self.deployed_count}")
        print(f"[ERROR] Failed deployments: {self.failed_count}")
        print(f"[TOTAL] Total servers: {self.deployed_count + self.failed_count}")
        
        if self.results:
            print("\n[RESULTS] Detailed Results:")
            for result in self.results:
                status_icon = "[SUCCESS]" if result['status'] == 'success' else "[WARNING]" if result['status'] == 'warning' else "[ERROR]"
                print(f"   {status_icon} {result['server']}: {result['message']}")
        
        if self.deployed_count > 0:
            print(f"\n[SUCCESS] {self.deployed_count} agents are now running!")
            print("[INFO] Monitor agent status at: /api/agent/status/")
        
        if self.failed_count > 0:
            print(f"\n[ERROR] {self.failed_count} deployments need attention")
            print("[INFO] Check SSH credentials and server connectivity")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Automated Agent Deployment')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be deployed without actually deploying')
    parser.add_argument('--list', action='store_true', help='List servers with SSH credentials')
    parser.add_argument('--target-ip', help='Deploy only to a specific server by IP address')
    
    args = parser.parse_args()
    
    deployer = AutomatedAgentDeployer()
    
    if args.list:
        servers_with_creds = deployer.get_servers_with_credentials()
        print(f"[LIST] Servers with SSH credentials: {len(servers_with_creds)}")
        print("-" * 50)
        for i, server_cred in enumerate(servers_with_creds, 1):
            server = server_cred['server']
            cred = server_cred['credential']
            print(f"{i}. {server.name} ({server.ip_address})")
            print(f"   User: {cred.username}")
            print(f"   Port: {cred.port}")
            print(f"   Auth: {{'Key' if cred.use_key else 'Password'}}")
            print()
    elif args.dry_run:
        servers_with_creds = deployer.get_servers_with_credentials()
        if args.target_ip:
            servers_with_creds = [sc for sc in servers_with_creds if str(sc['server'].ip_address) == args.target_ip]
        print(f"🔍 Dry run - Would deploy to {len(servers_with_creds)} servers:")
        for server_cred in servers_with_creds:
            server = server_cred['server']
            print(f"   - {server.name} ({server.ip_address})")
    else:
        # Pass target_ip to deploy_to_all
        deployer.deploy_to_all(target_ip=args.target_ip)

if __name__ == "__main__":
    main()
