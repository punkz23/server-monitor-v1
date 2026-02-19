# SSL Certificate Auto-Check Setup Guide

## Overview
Your ServerWatch system now includes automatic SSL certificate monitoring with multiple scheduling options.

## Scheduling Options

### 1. Built-in Django Scheduler (Recommended)
The system now includes a built-in scheduler that starts automatically when Django runs:

- **Every 6 hours**: Certificate status check (no alerts)
- **Daily at 08:00**: Full certificate check with alerts

This scheduler is built into the `monitor` app and starts automatically when Django initializes.

### 2. Windows Task Scheduler
For more robust scheduling on Windows:

```bash
# Setup the automated task
python setup_daily_task.py

# Manual commands
schtasks /run /tn "ServerWatch_Daily_Certificate_Check"  # Test run
schtasks /delete /tn "ServerWatch_Daily_Certificate_Check" /f  # Remove
```

### 3. Manual/CLI Options
```bash
# Check all certificates now
python manage.py check_certificates

# Daily check with alerts
python manage.py daily_cert_check

# Batch file for manual execution
daily_cert_check.bat
```

## Alert Thresholds

Certificates are monitored with these default thresholds:
- **Warning**: ≤30 days until expiry
- **Critical**: ≤7 days until expiry  
- **Expired**: 0 days or negative

## Current Certificate Status

**ho.employee.dailyoverland.com**
- Days until expiry: 21 days
- Status: ⚠️ WARNING
- Domains: 8 total (including www.ho-dtr.dailyoverland.com)
- Expires: February 24, 2026

## Dashboard Features

- Real-time certificate status display
- Summary statistics (valid/warning/critical/expired)
- Individual certificate cards
- Manual refresh and check buttons
- Color-coded status indicators

## Automation Notes

1. **Built-in scheduler** runs automatically when Django server is running
2. **Windows Task Scheduler** provides system-level automation even when Django isn't running
3. **Alerts** are created automatically during daily checks
4. **Exit codes** for automation integration:
   - 0: All certificates healthy
   - 1: Warning certificates exist
   - 2: Critical/expired certificates exist

## Monitoring Logs

Certificate checks are logged to the console with timestamps:
```
[2026-02-03 08:00:00] Running daily certificate check with alerts...
[2026-02-03 14:00:00] Certificate check: 1/1 successful
```

The system is now fully automated and will monitor your SSL certificates continuously!
