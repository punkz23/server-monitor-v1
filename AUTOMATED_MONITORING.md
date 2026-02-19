# Automated Server Status Monitoring

This system provides automated status updates for all servers in your monitoring dashboard.

## 🚀 Quick Start

### Method 1: Manual Command
```bash
# Update all server statuses once
python manage.py update_server_status --verbose

# Start automated monitoring (runs every 5 minutes)
python manage.py monitor_status start --interval 300

# Check monitoring status
python manage.py monitor_status status

# Stop automated monitoring
python manage.py monitor_status stop
```

### Method 2: Batch Scripts (Windows)
- **Start**: `start_monitoring.bat`
- **Stop**: `stop_monitoring.bat`
- **Check Status**: `check_monitoring.bat`
- **Setup Scheduled Task**: `setup_scheduled_task.bat` (run as Administrator)

### Method 3: Windows Task Scheduler
Run `setup_scheduled_task.bat` as Administrator to create a scheduled task that runs monitoring every 5 minutes.

## 📋 Features

### ✅ What It Does
- **Automatic Status Updates**: Checks all enabled servers every 5 minutes
- **Multiple Check Methods**: HTTP, HTTPS, port checks, and ping
- **Smart Detection**: Any HTTP response means server is UP (even 500 errors)
- **Real-time Updates**: Updates dashboard immediately
- **Logging**: Tracks status changes in logs
- **Background Service**: Runs without blocking other operations

### 🔍 Check Methods (in order)
1. **HTTP Request** - `http://IP` (most reliable for web servers)
2. **HTTPS Request** - `https://IP` (with SSL verification disabled)
3. **Port 80 Check** - Direct socket connection
4. **Port 443 Check** - Direct SSL socket connection
5. **Ping** - ICMP ping (last resort)

### ⚙️ Configuration Options
- **Check Interval**: Default 300 seconds (5 minutes)
- **Timeout**: 5 seconds per check
- **Verbose Mode**: Detailed output
- **Single Server**: Check specific IP only

## 🛠️ Management Commands

### update_server_status
```bash
# Update all servers
python manage.py update_server_status

# Update specific server
python manage.py update_server_status --server-ip 192.168.254.19

# Verbose output
python manage.py update_server_status --verbose

# Custom timeout
python manage.py update_server_status --timeout 10
```

### monitor_status
```bash
# Start monitoring (5 minute interval)
python manage.py monitor_status start

# Start with custom interval (2 minutes)
python manage.py monitor_status start --interval 120

# Check status
python manage.py monitor_status status

# Stop monitoring
python manage.py monitor_status stop

# Run in foreground (for testing)
python manage.py monitor_status run --interval 60
```

## 📊 Status Information

### Dashboard Updates
- **Server List**: Shows UP/DOWN status in real-time
- **Network Overview**: Displays uptime percentage
- **Statistics**: Total servers, up count, down count
- **Last Checked**: Timestamp of last status check

### Status Values
- **UP**: Server is responding to requests
- **DOWN**: Server is not responding
- **UNKNOWN**: Server hasn't been checked recently

## 🔧 Troubleshooting

### Common Issues

#### Server Shows DOWN but is UP
- **Cause**: Server returning HTTP 500+ errors
- **Fix**: System now treats any HTTP response as UP
- **Check**: `python manage.py update_server_status --verbose --server-ip IP`

#### Monitoring Not Running
- **Check Status**: `python manage.py monitor_status status`
- **Restart**: `python manage.py monitor_status stop` then `start`
- **Check Logs**: Look for errors in Django logs

#### Scheduled Task Not Working
- **Run as Administrator**: Required for Task Scheduler
- **Check Task**: `schtasks /query /tn "ServerStatusMonitoring"`
- **Run Manually**: `python manage.py update_server_status`

### Performance Considerations
- **Check Interval**: 5 minutes is recommended (don't set too low)
- **Timeout**: 5 seconds is good balance (adjust if needed)
- **Server Count**: Works efficiently with 50+ servers
- **Network Load**: Minimal impact on network traffic

## 📝 Logs and Monitoring

### Django Logging
Status changes are logged to Django's logging system:
- Server UP transitions
- Server DOWN transitions
- Error conditions
- Performance metrics

### Manual Log Check
```bash
# View recent status changes
python manage.py shell -c "
from monitor.models import Server
from django.utils import timezone
from datetime import timedelta

recent = timezone.now() - timedelta(hours=1)
servers = Server.objects.filter(last_checked__gte=recent)
for s in servers:
    print(f'{s.name}: {s.last_status} at {s.last_checked}')
"
```

## 🔄 Automation Options

### Option 1: Background Service
```python
# In your Django app or management command
from monitor.services.server_status_monitor import start_automated_monitoring

# Start monitoring (runs forever in background)
monitor = start_automated_monitoring()
```

### Option 2: Windows Task Scheduler
- **Setup**: Run `setup_scheduled_task.bat` as Administrator
- **Frequency**: Every 5 minutes
- **User**: SYSTEM account
- **Command**: `python manage.py update_server_status`

### Option 3: Cron Job (Linux)
```bash
# Add to crontab: crontab -e
*/5 * * * * cd /path/to/django-serverwatch && python manage.py update_server_status
```

## 🎯 Best Practices

1. **Start with Manual Testing**: Use `--verbose` to test specific servers
2. **Use Appropriate Intervals**: 5 minutes is good for most cases
3. **Monitor Logs**: Check for patterns in server failures
4. **Handle False Positives**: Some services return 500 but are still up
5. **Regular Maintenance**: Review and update server list periodically

## 🚨 Alerts and Notifications

The system updates the dashboard automatically. For email/SMS alerts, you can extend the system by:
- Adding alert rules in Django admin
- Integrating with notification services
- Setting up custom webhook notifications

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Run `python manage.py monitor_status status` for diagnostics
3. Use `--verbose` flag for detailed output
4. Check Django logs for error messages
