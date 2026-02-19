#!/usr/bin/env python3
"""
Start ServerWatch Agents Without Server Restart
This script starts existing agents without full redeployment
"""

import os
import sys
import django
import paramiko
import json
import time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.models import Server
from monitor.models_ssh_credentials import SSHCredential

class AgentStarter:
    def __init__(self):
        self.started_count = 0
        self.failed_count = 0
        self.results = []
        
    def get_servers_with_agents(self):
        """Get servers that have agents installed"""
        servers_with_agents = []
        
        for server in Server.objects.filter(enabled=True):
            try:
                cred = server.ssh_credential
                if cred and cred.is_active and server.agent_token:
                    servers_with_agents.append({
                        'server': server,
                        'credential': cred,
                        'agent_status': server.agent_status or 'unknown',
                        'last_heartbeat': server.last_agent_heartbeat
                    })
            except:
                continue
                
        return servers_with_agents
    
    def start_agent_on_server(self, server, credential):
        """Start agent on a specific server"""
        hostname = server.ip_address
        server_name = server.name
        
        print(f"[START] Starting agent on {server_name} ({hostname})...")
        
        try:
            # Create SSH connection
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect using SSH credentials
            if credential.private_key_path:
                key = paramiko.RSAKey.from_private_key_file(credential.private_key_path)
                ssh.connect(
                    hostname, 
                    username=credential.username,
                    pkey=key,
                    port=credential.port,
                    timeout=30
                )
            else:
                ssh.connect(
                    hostname,
                    username=credential.username,
                    password=credential.get_password(),
                    port=credential.port,
                    timeout=30
                )
            
            # Check if agent is installed first
            stdin, stdout, stderr = ssh.exec_command("test -f /opt/serverwatch-agent/serverwatch-agent.py && echo 'installed' || echo 'not_installed'")
            agent_installed = stdout.read().decode().strip()
            
            if agent_installed != 'installed':
                print(f"[ERROR] Agent not installed on {server_name}")
                self.results.append({
                    'server': server_name,
                    'status': 'error',
                    'message': 'Agent not installed'
                })
                self.failed_count += 1
                ssh.close()
                return
            
            # Start agent service
            stdin, stdout, stderr = ssh.exec_command("sudo systemctl start serverwatch-agent")
            
            # Check service status
            stdin, stdout, stderr = ssh.exec_command("sudo systemctl is-active serverwatch-agent")
            service_status = stdout.read().decode().strip()
            
            if service_status == "active":
                print(f"[SUCCESS] Agent started successfully on {server_name}")
                
                # Update server record
                server.agent_status = "online"
                server.last_agent_heartbeat = timezone.now()
                server.save(update_fields=['agent_status', 'last_agent_heartbeat'])
                
                self.results.append({
                    'server': server_name,
                    'status': 'success',
                    'message': 'Agent started successfully'
                })
                self.started_count += 1
            else:
                error = stderr.read().decode()
                print(f"[ERROR] Failed to start agent on {server_name}: {error}")
                self.results.append({
                    'server': server_name,
                    'status': 'error',
                    'message': f'Failed to start: {error}'
                })
                self.failed_count += 1
            
            ssh.close()
            
        except Exception as e:
            print(f"[ERROR] Error starting agent on {server_name}: {e}")
            self.results.append({
                'server': server_name,
                'status': 'error',
                'message': str(e)
            })
            self.failed_count += 1
    
    def start_all_agents(self):
        """Start all agents that are installed but not running"""
        servers_with_agents = self.get_servers_with_agents()
        
        if not servers_with_agents:
            print("[INFO] No servers with installed agents found")
            return
        
        print(f"[START] Starting agents on {len(servers_with_agents)} servers...")
        print("=" * 60)
        
        # Start each agent
        for i, server_cred in enumerate(servers_with_agents, 1):
            server = server_cred['server']
            credential = server_cred['credential']
            
            print(f"[{i}/{len(servers_with_agents)}] ", end="")
            
            # Only start if agent is not already online
            if server.agent_status != 'online':
                self.start_agent_on_server(server, credential)
            else:
                print(f"[SKIP] {server.name} - Agent already online")
                self.results.append({
                    'server': server.name,
                    'status': 'skipped',
                    'message': 'Agent already running'
                })
            
            # Small delay between starts
            time.sleep(2)
        
        self.print_summary()
    
    def print_summary(self):
        """Print start summary"""
        print("\n" + "=" * 60)
        print("[SUMMARY] AGENT START SUMMARY")
        print("=" * 60)
        
        print(f"[SUCCESS] Successfully started: {self.started_count}")
        print(f"[SKIPPED] Already running: {len([r for r in self.results if r['status'] == 'skipped'])}")
        print(f"[ERROR] Failed to start: {self.failed_count}")
        print(f"[TOTAL] Total servers: {self.started_count + self.failed_count + len([r for r in self.results if r['status'] == 'skipped'])}")
        
        if self.results:
            print("\n[RESULTS] Detailed Results:")
            for result in self.results:
                status_icon = "[SUCCESS]" if result['status'] == 'success' else "[SKIP]" if result['status'] == 'skipped' else "[ERROR]"
                print(f"   {status_icon} {result['server']}: {result['message']}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Start ServerWatch Agents')
    parser.add_argument('--list', action='store_true', help='List servers with installed agents')
    parser.add_argument('--server-id', type=int, help='Start agent on specific server ID')
    
    args = parser.parse_args()
    
    starter = AgentStarter()
    
    if args.list:
        servers_with_agents = starter.get_servers_with_agents()
        print(f"[LIST] Servers with installed agents: {len(servers_with_agents)}")
        print("-" * 50)
        for i, server_cred in enumerate(servers_with_agents, 1):
            server = server_cred['server']
            cred = server_cred['credential']
            print(f"{i}. {server.name} ({server.ip_address})")
            print(f"   Status: {server.agent_status or 'unknown'}")
            print(f"   Last Heartbeat: {server.last_agent_heartbeat or 'Never'}")
            print()
    elif args.server_id:
        try:
            server = Server.objects.get(id=args.server_id)
            cred = server.ssh_credential
            
            if not cred or not cred.is_active or not server.agent_token:
                print(f"[ERROR] Server {server.name} has no agent installed")
                return
            
            starter.start_agent_on_server(server, cred)
        except Server.DoesNotExist:
            print(f"[ERROR] Server with ID {args.server_id} not found")
    else:
        starter.start_all_agents()

if __name__ == "__main__":
    main()
