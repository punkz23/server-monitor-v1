#!/usr/bin/env python3
"""
Server Agent Deployment Script
Deploys monitoring agents to remote servers for real-time metrics collection
"""

import os
import sys
import argparse
import json
import subprocess
import paramiko
from pathlib import Path

class AgentDeployer:
    def __init__(self, config_file="agent_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        
    def load_config(self):
        """Load agent configuration"""
        default_config = {
            "agent_version": "1.0.0",
            "install_path": "/opt/serverwatch-agent",
            "service_name": "serverwatch-agent",
            "port": 8765,
            "log_level": "INFO",
            "metrics_interval": 30,
            "heartbeat_interval": 60,
            "ssh_port": 22,
            "ssh_timeout": 30,
            "servers": []
        }
        
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        else:
            self.save_config(default_config)
            
        return default_config
    
    def save_config(self, config=None):
        """Save configuration to file"""
        if config is None:
            config = self.config
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def create_agent_files(self):
        """Create agent files for deployment"""
        agent_dir = Path("agent_files")
        agent_dir.mkdir(exist_ok=True)
        
        # Create main agent script
        agent_script = '''#!/usr/bin/env python3
"""
ServerWatch Agent
Real-time server monitoring agent
"""

import os
import sys
import time
import json
import psutil
import socket
import requests
import logging
import threading
from datetime import datetime
from pathlib import Path

class ServerAgent:
    def __init__(self, config_file="/etc/serverwatch-agent/config.json"):
        self.config = self.load_config(config_file)
        self.setup_logging()
        self.running = False
        self.server_id = self.get_server_id()
        
    def load_config(self, config_file):
        """Load agent configuration"""
        default_config = {
            "server_url": "http://localhost:8000",
            "agent_token": "",
            "port": 8765,
            "metrics_interval": 30,
            "heartbeat_interval": 60,
            "log_level": "INFO"
        }
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        return default_config
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, self.config["log_level"]),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/var/log/serverwatch-agent.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_server_id(self):
        """Generate unique server ID"""
        try:
            # Get MAC address for unique identification
            mac = ':'.join(['{:02x}'.format((psutil.net_if_addrs().get(list(psutil.net_if_addrs().keys())[0])[0].address).replace(':', '')[i:i+2]) for i in range(0, 12, 2)])
            hostname = socket.gethostname()
            return f"{hostname}-{mac[:8]}"
        except:
            return socket.gethostname()
    
    def get_system_metrics(self):
        """Collect system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            
            # Network metrics
            network = psutil.net_io_counters()
            
            # Process metrics
            process_count = len(psutil.pids())
            
            # System uptime
            uptime = time.time() - psutil.boot_time()
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "server_id": self.server_id,
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count,
                    "load_1m": load_avg[0],
                    "load_5m": load_avg[1],
                    "load_15m": load_avg[2]
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used,
                    "free": memory.free
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                },
                "system": {
                    "uptime_seconds": uptime,
                    "process_count": process_count,
                    "hostname": socket.gethostname()
                }
            }
        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}")
            return None
    
    def send_heartbeat(self):
        """Send heartbeat to server"""
        try:
            payload = {
                "server_id": self.server_id,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "online",
                "agent_version": "1.0.0"
            }
            
            response = requests.post(
                f"{self.config['server_url']}/api/agent/heartbeat/",
                json=payload,
                headers={"Authorization": f"Bearer {self.config['agent_token']}"},
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.debug("Heartbeat sent successfully")
            else:
                self.logger.warning(f"Heartbeat failed: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Heartbeat error: {e}")
    
    def send_metrics(self, metrics):
        """Send metrics to server"""
        try:
            response = requests.post(
                f"{self.config['server_url']}/api/agent/metrics/",
                json=metrics,
                headers={"Authorization": f"Bearer {self.config['agent_token']}"},
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.debug("Metrics sent successfully")
            else:
                self.logger.warning(f"Metrics send failed: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Metrics send error: {e}")
    
    def metrics_loop(self):
        """Main metrics collection loop"""
        while self.running:
            try:
                metrics = self.get_system_metrics()
                if metrics:
                    self.send_metrics(metrics)
                time.sleep(self.config["metrics_interval"])
            except Exception as e:
                self.logger.error(f"Metrics loop error: {e}")
                time.sleep(5)
    
    def heartbeat_loop(self):
        """Heartbeat loop"""
        while self.running:
            try:
                self.send_heartbeat()
                time.sleep(self.config["heartbeat_interval"])
            except Exception as e:
                self.logger.error(f"Heartbeat loop error: {e}")
                time.sleep(5)
    
    def start(self):
        """Start the agent"""
        self.logger.info(f"Starting ServerWatch Agent - Server ID: {self.server_id}")
        self.running = True
        
        # Start metrics collection thread
        metrics_thread = threading.Thread(target=self.metrics_loop, daemon=True)
        metrics_thread.start()
        
        # Start heartbeat thread
        heartbeat_thread = threading.Thread(target=self.heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Shutting down agent...")
            self.running = False
    
    def stop(self):
        """Stop the agent"""
        self.running = False

def main():
    import argparse
    parser = argparse.ArgumentParser(description='ServerWatch Agent')
    parser.add_argument('--config', default='/etc/serverwatch-agent/config.json', help='Configuration file path')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    args = parser.parse_args()
    
    agent = ServerAgent(args.config)
    
    if args.daemon:
        import daemon
        with daemon.DaemonContext():
            agent.start()
    else:
        agent.start()

if __name__ == "__main__":
    main()
'''
        
        # Write agent script
        with open(agent_dir / "serverwatch-agent.py", 'w') as f:
            f.write(agent_script)
        
        # Create service file
        service_file = '''[Unit]
Description=ServerWatch Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/serverwatch-agent
ExecStart=/opt/serverwatch-agent/venv/bin/python /opt/serverwatch-agent/serverwatch-agent.py --daemon
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
'''
        
        with open(agent_dir / "serverwatch-agent.service", 'w') as f:
            f.write(service_file)
        
        # Create requirements file
        requirements = '''psutil>=5.9.0
requests>=2.28.0
'''
        
        with open(agent_dir / "requirements.txt", 'w') as f:
            f.write(requirements)
        
        # Create install script
        install_script = '''#!/bin/bash
set -e

AGENT_DIR="/opt/serverwatch-agent"
SERVICE_NAME="serverwatch-agent"

echo "Installing ServerWatch Agent..."

# Create agent directory
sudo mkdir -p $AGENT_DIR
sudo cp serverwatch-agent.py $AGENT_DIR/
sudo cp requirements.txt $AGENT_DIR/
sudo cp serverwatch-agent.service /etc/systemd/system/

# Create virtual environment
cd $AGENT_DIR
sudo python3 -m venv venv
sudo $AGENT_DIR/venv/bin/pip install -r requirements.txt

# Create log directory
sudo mkdir -p /var/log
sudo touch /var/log/serverwatch-agent.log
sudo chmod 666 /var/log/serverwatch-agent.log

# Make agent executable
sudo chmod +x $AGENT_DIR/serverwatch-agent.py

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME

echo "Installation complete!"
echo "Configure the agent in /etc/serverwatch-agent/config.json"
echo "Then start with: sudo systemctl start $SERVICE_NAME"
'''
        
        with open(agent_dir / "install.sh", 'w') as f:
            f.write(install_script)
        
        # Make install script executable
        os.chmod(agent_dir / "install.sh", 0o755)
        
        print(f"✅ Agent files created in {agent_dir}/")
        return agent_dir
    
    def deploy_to_server(self, server_info):
        """Deploy agent to a single server"""
        hostname = server_info["hostname"]
        username = server_info.get("username", "root")
        password = server_info.get("password")
        key_file = server_info.get("key_file")
        port = server_info.get("port", self.config["ssh_port"])
        
        print(f"🚀 Deploying agent to {hostname}...")
        
        try:
            # Create SSH connection
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if key_file:
                ssh.connect(hostname, username=username, key_filename=key_file, port=port, timeout=self.config["ssh_timeout"])
            else:
                ssh.connect(hostname, username=username, password=password, port=port, timeout=self.config["ssh_timeout"])
            
            # Create agent files
            agent_dir = self.create_agent_files()
            
            # Transfer files using SFTP
            sftp = ssh.open_sftp()
            
            # Transfer agent files
            for filename in ["serverwatch-agent.py", "requirements.txt", "serverwatch-agent.service", "install.sh"]:
                local_path = agent_dir / filename
                remote_path = f"/tmp/{filename}"
                sftp.put(str(local_path), remote_path)
            
            # Run installation
            stdin, stdout, stderr = ssh.exec_command("cd /tmp && sudo bash install.sh")
            
            # Wait for completion
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0:
                print(f"✅ Agent deployed successfully to {hostname}")
                
                # Create configuration
                config = {
                    "server_url": server_info.get("server_url", "http://localhost:8000"),
                    "agent_token": server_info.get("agent_token", ""),
                    "port": self.config["port"],
                    "metrics_interval": self.config["metrics_interval"],
                    "heartbeat_interval": self.config["heartbeat_interval"],
                    "log_level": self.config["log_level"]
                }
                
                # Transfer configuration
                sftp.putfo(
                    json.dumps(config, indent=2).encode(),
                    "/tmp/config.json"
                )
                
                # Install configuration
                stdin, stdout, stderr = ssh.exec_command("sudo mkdir -p /etc/serverwatch-agent && sudo mv /tmp/config.json /etc/serverwatch-agent/")
                
                # Start service if requested
                if server_info.get("start_service", True):
                    stdin, stdout, stderr = ssh.exec_command("sudo systemctl start serverwatch-agent")
                    print(f"🔄 Agent service started on {hostname}")
                
            else:
                error = stderr.read().decode()
                print(f"❌ Deployment failed on {hostname}: {error}")
            
            sftp.close()
            ssh.close()
            
        except Exception as e:
            print(f"❌ Error deploying to {hostname}: {e}")
    
    def deploy_to_all(self):
        """Deploy to all configured servers"""
        if not self.config["servers"]:
            print("❌ No servers configured in config file")
            return
        
        print(f"🚀 Deploying to {len(self.config['servers'])} servers...")
        
        for server in self.config["servers"]:
            self.deploy_to_server(server)
    
    def add_server(self, hostname, username=None, password=None, key_file=None, **kwargs):
        """Add server to configuration"""
        server_info = {
            "hostname": hostname,
            "username": username or "root"
        }
        
        if password:
            server_info["password"] = password
        if key_file:
            server_info["key_file"] = key_file
        
        server_info.update(kwargs)
        
        self.config["servers"].append(server_info)
        self.save_config()
        print(f"✅ Server {hostname} added to configuration")

def main():
    parser = argparse.ArgumentParser(description='Deploy ServerWatch agents')
    parser.add_argument('--config', default='agent_config.json', help='Configuration file')
    parser.add_argument('--add-server', help='Add server to configuration')
    parser.add_argument('--username', help='SSH username')
    parser.add_argument('--password', help='SSH password')
    parser.add_argument('--key-file', help='SSH private key file')
    parser.add_argument('--server-url', help='Server URL for agents')
    parser.add_argument('--agent-token', help='Agent authentication token')
    parser.add_argument('--create-files', action='store_true', help='Create agent files only')
    parser.add_argument('--deploy-all', action='store_true', help='Deploy to all configured servers')
    
    args = parser.parse_args()
    
    deployer = AgentDeployer(args.config)
    
    if args.create_files:
        deployer.create_agent_files()
    elif args.add_server:
        deployer.add_server(
            hostname=args.add_server,
            username=args.username,
            password=args.password,
            key_file=args.key_file,
            server_url=args.server_url,
            agent_token=args.agent_token
        )
    elif args.deploy_all:
        deployer.deploy_to_all()
    else:
        print("Use --create-files, --add-server, or --deploy-all")

if __name__ == "__main__":
    main()
