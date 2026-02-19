# ServerWatch Agent Deployment Guide

This guide covers deploying ServerWatch agents to servers for real-time monitoring and metrics collection.

## Overview

ServerWatch agents are lightweight Python applications that run on monitored servers and:
- Collect system metrics (CPU, RAM, Disk, Network)
- Send real-time data to the central ServerWatch instance
- Provide heartbeat status for connectivity monitoring
- Support both Linux and Windows platforms

## Quick Start

### 1. Generate Agent Tokens

```bash
# Generate token for all servers
python manage.py generate_agent_tokens --all

# Generate token for specific server
python manage.py generate_agent_tokens --server-id 1

# Regenerate existing tokens
python manage.py generate_agent_tokens --all --regenerate
```

### 2. Deploy to Linux Servers

```bash
# Create agent configuration
python deploy_agents.py --add-server 192.168.1.100 --username root --password yourpassword --server-url http://your-server:8000 --agent-token TOKEN_HERE

# Deploy to all configured servers
python deploy_agents.py --deploy-all

# Create agent files only (for manual deployment)
python deploy_agents.py --create-files
```

### 3. Deploy to Windows Servers

1. Copy `deploy_agent_windows.bat` to the Windows server
2. Run as Administrator
3. Edit `C:\ServerWatch-Agent\config.json` with your server URL and token
4. Restart the service

## Agent Configuration

### Configuration File Location
- **Linux**: `/etc/serverwatch-agent/config.json`
- **Windows**: `C:\ServerWatch-Agent\config.json`

### Configuration Options

```json
{
  "server_url": "http://your-serverwatch-server:8000",
  "agent_token": "generated-secure-token-here",
  "port": 8765,
  "metrics_interval": 30,
  "heartbeat_interval": 60,
  "log_level": "INFO"
}
```

| Option | Description | Default |
|---------|-------------|---------|
| `server_url` | URL of ServerWatch server | Required |
| `agent_token` | Authentication token | Required |
| `port` | Agent port | 8765 |
| `metrics_interval` | Metrics collection interval (seconds) | 30 |
| `heartbeat_interval` | Heartbeat interval (seconds) | 60 |
| `log_level` | Logging level | INFO |

## Deployment Methods

### Method 1: Automated Deployment (Recommended)

```bash
# Install deployment dependencies
pip install paramiko

# Configure servers
python deploy_agents.py --add-server 192.168.1.100 \
    --username root \
    --password yourpassword \
    --server-url http://monitor.company.com:8000 \
    --agent-token your-token-here

# Deploy to all servers
python deploy_agents.py --deploy-all
```

### Method 2: Manual Linux Deployment

```bash
# Download agent files
wget http://your-server:8000/static/agent/serverwatch-agent.py
wget http://your-server:8000/static/agent/requirements.txt

# Install dependencies
sudo apt update
sudo apt install -y python3 python3-pip python3-venv

# Create agent directory
sudo mkdir -p /opt/serverwatch-agent
cd /opt/serverwatch-agent

# Setup virtual environment
sudo python3 -m venv venv
sudo venv/bin/pip install -r requirements.txt

# Install agent
sudo cp serverwatch-agent.py /opt/serverwatch-agent/
sudo chmod +x /opt/serverwatch-agent/serverwatch-agent.py

# Create configuration
sudo mkdir -p /etc/serverwatch-agent
sudo nano /etc/serverwatch-agent/config.json

# Install and start service
sudo cp serverwatch-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable serverwatch-agent
sudo systemctl start serverwatch-agent
```

### Method 3: Manual Windows Deployment

1. Download `deploy_agent_windows.bat`
2. Run as Administrator
3. Edit configuration file at `C:\ServerWatch-Agent\config.json`
4. Restart the service

## Agent Features

### Metrics Collection

The agent collects the following metrics:

#### System Metrics
- **CPU**: Usage percentage, core count, load averages
- **Memory**: Total, used, free, usage percentage
- **Disk**: Total, used, free, usage percentage
- **Network**: Bytes sent/received, packets sent/received
- **System**: Uptime, process count, hostname

#### Real-time Features
- **Heartbeat**: Regular status updates every 60 seconds
- **Metrics**: Detailed metrics every 30 seconds
- **Auto-restart**: Service restarts on failure
- **Logging**: Comprehensive logging for troubleshooting

### Security Features

- **Token Authentication**: Secure token-based authentication
- **HTTPS Support**: Encrypted communication (optional)
- **Firewall Friendly**: Minimal port requirements
- **Audit Logging**: All actions logged

## API Endpoints

The agent communicates with these ServerWatch API endpoints:

| Endpoint | Method | Purpose |
|----------|---------|---------|
| `/api/agent/heartbeat/` | POST | Send heartbeat status |
| `/api/agent/metrics/` | POST | Send system metrics |
| `/api/agent/status/` | GET | Get agent status |

## Troubleshooting

### Common Issues

#### Agent Not Starting
```bash
# Check service status (Linux)
sudo systemctl status serverwatch-agent

# Check service status (Windows)
sc query ServerWatchAgent

# View logs
sudo journalctl -u serverwatch-agent -f
```

#### Authentication Errors
1. Verify agent token is correct
2. Check server URL is accessible
3. Ensure firewall allows outbound connections

#### Connection Issues
```bash
# Test connectivity from agent to server
curl -X POST http://your-server:8000/api/agent/heartbeat/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"server_id":"test","status":"online"}'
```

#### Performance Issues
1. Increase `metrics_interval` in configuration
2. Check system resources on agent server
3. Monitor network bandwidth usage

### Log Locations

- **Linux**: `/var/log/serverwatch-agent.log`
- **Windows**: `C:\ServerWatch-Agent\agent.log`
- **Systemd**: `journalctl -u serverwatch-agent`

### Service Management

#### Linux (systemd)
```bash
sudo systemctl start serverwatch-agent
sudo systemctl stop serverwatch-agent
sudo systemctl restart serverwatch-agent
sudo systemctl enable serverwatch-agent
sudo systemctl disable serverwatch-agent
```

#### Windows
```cmd
sc start ServerWatchAgent
sc stop ServerWatchAgent
sc query ServerWatchAgent
```

## Monitoring Agent Status

### Web Interface
1. Go to ServerWatch dashboard
2. Navigate to Agent Status page
3. View online/offline status and last heartbeat

### API
```bash
# Get all agent status
curl http://your-server:8000/api/agent/status/

# Response format
{
  "agents": [
    {
      "id": 1,
      "name": "web-server-01",
      "ip_address": "192.168.1.100",
      "agent_status": "online",
      "agent_version": "1.0.0",
      "last_heartbeat": "2024-01-20T10:30:00Z",
      "last_metrics": "2024-01-20T10:29:30Z",
      "is_online": true,
      "seconds_since_heartbeat": 45
    }
  ],
  "total_servers": 1,
  "online_agents": 1,
  "timestamp": "2024-01-20T10:30:45Z"
}
```

## Security Considerations

### Network Security
- Use HTTPS for production deployments
- Configure firewall rules appropriately
- Monitor agent communication

### Token Security
- Generate unique tokens for each server
- Rotate tokens periodically
- Store tokens securely

### System Security
- Run agents with minimal privileges
- Regular security updates
- Monitor agent file integrity

## Performance Optimization

### Agent Configuration
- Adjust `metrics_interval` based on requirements
- Use appropriate log levels
- Monitor resource usage

### Server Configuration
- Implement database indexes for metrics
- Use caching for frequently accessed data
- Consider load balancing for large deployments

## Advanced Features

### Custom Metrics
Extend the agent to collect application-specific metrics:

```python
def get_custom_metrics(self):
    """Collect custom application metrics"""
    return {
        "app_users": get_active_users(),
        "app_requests": get_request_count(),
        "app_errors": get_error_count()
    }
```

### Alerts and Notifications
Configure alerts based on agent data:
- Agent offline notifications
- High resource usage alerts
- Custom metric thresholds

## Support

For issues and questions:
1. Check agent logs
2. Verify network connectivity
3. Review configuration
4. Check ServerWatch server logs
5. Consult troubleshooting section

## Version History

- **v1.0.0**: Initial release with basic metrics and heartbeat
- Future versions will include:
  - Custom metrics support
  - Plugin system
  - Enhanced security features
  - Performance improvements
