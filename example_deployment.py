#!/usr/bin/env python3
"""
Example: Deploy ServerWatch Agents
This script demonstrates how to deploy agents to multiple servers
"""

import sys
import os

# Add project to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from deploy_agents import AgentDeployer

def main():
    """Example deployment"""
    print("🚀 ServerWatch Agent Deployment Example")
    print("=" * 50)
    
    # Initialize deployer
    deployer = AgentDeployer("example_config.json")
    
    # Add servers to configuration
    servers = [
        {
            "hostname": "192.168.1.100",
            "username": "root",
            "password": "your_password_here",
            "server_url": "http://your-serverwatch-server:8000",
            "agent_token": "generated_token_here",
            "start_service": True
        },
        {
            "hostname": "192.168.1.101", 
            "username": "admin",
            "key_file": "/path/to/ssh/key",
            "server_url": "http://your-serverwatch-server:8000",
            "agent_token": "generated_token_here",
            "start_service": True
        },
        {
            "hostname": "web-server.company.com",
            "username": "ubuntu",
            "key_file": "~/.ssh/web_server_key",
            "server_url": "http://monitor.company.com:8000", 
            "agent_token": "generated_token_here",
            "start_service": True
        }
    ]
    
    # Add servers to configuration
    for server in servers:
        deployer.add_server(**server)
    
    print(f"\n📋 Added {len(servers)} servers to configuration")
    print("Configuration saved to: example_config.json")
    
    # Option 1: Deploy to all servers
    print("\n🔄 Deploying to all servers...")
    deployer.deploy_to_all()
    
    # Option 2: Deploy to specific server
    # deployer.deploy_to_server(servers[0])
    
    print("\n✅ Deployment complete!")
    print("\nNext steps:")
    print("1. Generate agent tokens: python manage.py generate_agent_tokens --all")
    print("2. Update server configurations with generated tokens")
    print("3. Monitor agent status: http://your-server:8000/api/agent/status/")

if __name__ == "__main__":
    main()
