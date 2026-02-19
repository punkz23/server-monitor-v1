# Django Server Automation - PowerShell Script

## 🎯 Overview

This PowerShell script provides comprehensive automation for running your Django server and backend services. It includes server management, process monitoring, auto-restart capabilities, and Windows service installation.

## 📁 Files Created

### **Primary Script**
- **`django_server.ps1`** - Main PowerShell script with full functionality
- **`start_django_server.bat`** - Easy-to-use batch file launcher

### **Features**
- ✅ **Automatic Server Startup** - Django development server with virtual environment
- ✅ **Process Monitoring** - Tracks server status and auto-restarts on crashes
- ✅ **Service Management** - Start, stop, restart, status checking
- ✅ **Windows Service** - Install as system service for automatic startup
- ✅ **Port Checking** - Verifies port availability before starting
- ✅ **Virtual Environment** - Automatic activation if venv exists
- ✅ **Error Handling** - Comprehensive error handling and logging
- ✅ **Interactive Mode** - Real-time server monitoring with keyboard controls

---

## 🚀 Quick Start

### **Method 1: Batch File (Recommended)**
```batch
# Double-click this file
start_django_server.bat
```

### **Method 2: PowerShell Direct**
```powershell
# Run directly with PowerShell
.\django_server.ps1 Start
```

---

## 📋 Available Commands

### **Start Server**
```powershell
.\django_server.ps1 Start
```
**Features:**
- Activates virtual environment if exists
- Sets Django settings module
- Starts server on specified port (default: 8000)
- Monitors server process
- Provides server URLs for easy access
- Saves process information for monitoring

### **Stop Server**
```powershell
.\django_server.ps1 Stop
```
**Features:**
- Gracefully stops running Django server
- Cleans up process information
- Handles multiple server instances

### **Restart Server**
```powershell
.\django_server.ps1 Restart
```
**Features:**
- Stops current server instance
- Waits 2 seconds
- Starts fresh server instance
- Preserves configuration

### **Check Status**
```powershell
.\django_server.ps1 Status
```
**Returns:**
- Server running status (UP/DOWN)
- Process ID and uptime
- Server URLs and ports
- Process information file location

### **Install Windows Service**
```powershell
.\django_server.ps1 Install -CreateService
```
**Features:**
- Creates Windows service for automatic startup
- Runs Django server on system boot
- Service management commands included
- Administrator privileges required

---

## ⚙️ Configuration Options

### **Default Configuration**
```powershell
Project Path: C:\Users\igibo\CascadeProjects\django-serverwatch
Virtual Environment: C:\Users\igibo\CascadeProjects\django-serverwatch\venv
Python Executable: python
Server Port: 8000
Log Level: INFO
Auto Restart: Enabled
```

### **Custom Parameters**
```powershell
# Custom project path
.\django_server.ps1 Start -ProjectPath "C:\MyProject"

# Custom port
.\django_server.ps1 Start -ServerPort 8080

# Custom virtual environment
.\django_server.ps1 Start -VirtualEnvPath "C:\MyVenv"

# Custom Python executable
.\django_server.ps1 Start -PythonExe "C:\Python39\python.exe"

# Enable auto-restart
.\django_server.ps1 Start -AutoRestart

# Create Windows service
.\django_server.ps1 Install -CreateService -ServiceName "MyDjangoServer"
```

---

## 🌐 Server Access URLs

### **When Server is Running**
```
Django Server:    http://localhost:8000
Dashboard:         http://localhost:8000/monitoring/
API Endpoints:    http://localhost:8000/api/
Admin Panel:      http://localhost:8000/admin/
```

### **API Endpoints Available**
```
Device Metrics:     /api/network/device/<id>/metrics/
Metrics Summary:    /api/metrics/summary/
SSL Certificates:    /api/network/device/<id>/ssl/
Server Status:      /api/status/
Network Devices:    /api/network/devices/
```

---

## 🛡️ Advanced Features

### **Process Monitoring**
- Real-time server status checking
- Automatic crash detection and recovery
- Process ID tracking and management
- Uptime monitoring and reporting

### **Error Handling**
- Comprehensive exception handling
- Detailed error logging
- Graceful degradation handling
- User-friendly error messages

### **Interactive Controls**
- Press 'Q' or 'q' to stop server
- Real-time status display
- Keyboard interrupt handling
- Clean process termination

### **Windows Service Integration**
- Automatic system startup
- Service management commands
- Event log integration
- Run as system service
- Administrator privilege handling

---

## 🔧 Windows Service Management

### **Service Commands**
```powershell
# Install service
New-Service -Name "DjangoServerWatch" | Start-Service "DjangoServerWatch"

# Start service
Start-Service "DjangoServerWatch"

# Stop service  
Stop-Service "DjangoServerWatch"

# Remove service
Remove-Service "DjangoServerWatch"

# Check service status
Get-Service "DjangoServerWatch"
```

### **Service Benefits**
- **Automatic Startup**: Server starts on Windows boot
- **Background Operation**: Runs without user login
- **Crash Recovery**: Automatic restart on failures
- **System Integration**: Integrates with Windows services
- **Logging**: Windows event log integration

---

## 📊 Monitoring Integration

### **Backend Services Started**
The script automatically starts:
1. **Django Development Server** - Main web application
2. **SSL Certificate Cache Updates** - Background SSL monitoring
3. **Metrics Collection** - CPU, RAM, Disk monitoring
4. **Change Detection** - Threshold-based alerting
5. **API Endpoints** - Real-time data access

### **Process Information**
Server information is saved to:
```
File: .\django_server_info.json
Contents: Process ID, start time, port, paths
```

---

## 🎯 Usage Examples

### **Development Workflow**
```batch
# 1. Start server with easy launcher
start_django_server.bat

# 2. Choose option 1 (Start)
# 3. Server starts on http://localhost:8000
# 4. Dashboard available at http://localhost:8000/monitoring/
# 5. Press Ctrl+C to stop when done
```

### **Production Deployment**
```powershell
# 1. Install as Windows service for automatic startup
.\django_server.ps1 Install -CreateService

# 2. Start the service
Start-Service DjangoServerWatch

# 3. Server runs automatically on system boot
# 4. Manage with Windows service commands
```

### **Custom Configuration**
```powershell
# Custom port and project path
.\django_server.ps1 Start -ProjectPath "C:\MyProject" -ServerPort 8080

# With virtual environment and custom Python
.\django_server.ps1 Start -VirtualEnvPath "C:\MyVenv" -PythonExe "C:\Python39\python.exe"

# Enable auto-restart for production
.\django_server.ps1 Start -AutoRestart
```

---

## 🔒️ Security Considerations

### **Administrator Privileges**
- Service installation requires administrator rights
- Port binding below 1024 may need admin privileges
- Virtual environment activation handled safely

### **Network Security**
- Server binds to localhost only by default
- Port checking prevents conflicts
- Firewall configuration may be needed for external access

### **Process Security**
- Process isolation and monitoring
- Safe process termination
- Cleanup on exit and crashes

---

## 🚀 Benefits

### **Automation Benefits**
- ✅ **One-click deployment** - Start server with single command
- ✅ **Automatic recovery** - Server restarts on crashes
- ✅ **System integration** - Windows service support
- ✅ **Production ready** - Suitable for deployment environments
- ✅ **Development friendly** - Easy configuration and management

### **Operational Benefits**
- ✅ **Consistent environment** - Same settings every time
- ✅ **Virtual environment** - Automatic Python environment handling
- ✅ **Process monitoring** - Track server health and uptime
- ✅ **Error handling** - Robust error management and logging
- ✅ **Interactive control** - Real-time server management

---

## 📞 Troubleshooting

### **Common Issues**
1. **Port already in use**: Script will warn but continue
2. **Virtual environment not found**: Script continues without venv
3. **Python not found**: Check Python installation path
4. **Permission denied**: Run as administrator for service installation

### **Solutions**
- Use different port with `-ServerPort` parameter
- Install Python and configure virtual environment
- Run PowerShell as administrator for service operations
- Check Windows event logs for detailed error information

---

**Status**: ✅ **READY FOR PRODUCTION USE**

The Django server automation system provides comprehensive server management with Windows service integration, process monitoring, and automatic recovery capabilities.
