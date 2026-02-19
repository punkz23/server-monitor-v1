@echo off
REM ServerWatch Agent Deployment Script for Windows
REM This script installs the ServerWatch agent on Windows servers

setlocal enabledelayedexpansion

echo ========================================
echo ServerWatch Agent Deployment Script
echo ========================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator
    pause
    exit /b 1
)

REM Configuration
set AGENT_DIR=C:\ServerWatch-Agent
set SERVICE_NAME=ServerWatchAgent
set PYTHON_URL=https://www.python.org/ftp/python/3.11.5/python-3.11.5-amd64.exe
set PYTHON_EXE=%AGENT_DIR%\python\python.exe
set VENV_DIR=%AGENT_DIR%\venv

echo Installing ServerWatch Agent to %AGENT_DIR%
echo.

REM Create agent directory
if not exist "%AGENT_DIR%" (
    mkdir "%AGENT_DIR%"
)

REM Download and install Python if not exists
if not exist "%PYTHON_EXE%" (
    echo Downloading Python...
    powershell -Command "Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%AGENT_DIR%\python-installer.exe'"
    
    echo Installing Python...
    start /wait "" "%AGENT_DIR%\python-installer.exe" /quiet InstallAllUsers=0 TargetDir="%AGENT_DIR%\python" PrependPath=0
)

REM Create virtual environment
echo Creating virtual environment...
"%PYTHON_EXE%" -m venv "%VENV_DIR%"

REM Activate virtual environment and install requirements
echo Installing requirements...
"%VENV_DIR%\Scripts\pip.exe" install psutil requests

REM Create agent configuration
echo Creating configuration...
set CONFIG_FILE=%AGENT_DIR%\config.json
echo { > "%CONFIG_FILE%"
echo   "server_url": "http://your-server-url:8000", >> "%CONFIG_FILE%"
echo   "agent_token": "YOUR_AGENT_TOKEN_HERE", >> "%CONFIG_FILE%"
echo   "port": 8765, >> "%CONFIG_FILE%"
echo   "metrics_interval": 30, >> "%CONFIG_FILE%"
echo   "heartbeat_interval": 60, >> "%CONFIG_FILE%"
echo   "log_level": "INFO" >> "%CONFIG_FILE%"
echo } >> "%CONFIG_FILE%"

REM Download agent script
echo Downloading agent script...
powershell -Command "Invoke-WebRequest -Uri 'http://your-server-url:8000/static/agent/serverwatch-agent.py' -OutFile '%AGENT_DIR%\serverwatch-agent.py'"

REM Create Windows service
echo Creating Windows service...
sc create "%SERVICE_NAME%" binPath= "\"%VENV_DIR%\Scripts\python.exe\" \"%AGENT_DIR%\serverwatch-agent.py\"" start= auto
sc description "%SERVICE_NAME%" "ServerWatch Monitoring Agent"

REM Configure service recovery
sc failure "%SERVICE_NAME%" reset= 86400 actions= restart/5000/restart/10000/restart/20000

REM Start the service
echo Starting service...
sc start "%SERVICE_NAME%"

REM Create firewall rule
echo Creating firewall rule...
netsh advfirewall firewall add rule name="ServerWatch Agent" dir=in action=allow protocol=TCP localport=8765

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Agent installed and started as Windows service
echo Configuration file: %CONFIG_FILE%
echo.
echo IMPORTANT:
echo 1. Edit %CONFIG_FILE% and update:
echo    - server_url: Your ServerWatch server URL
echo    - agent_token: Generated agent token
echo.
echo 2. Restart service after configuration:
echo    sc stop "%SERVICE_NAME%"
echo    sc start "%SERVICE_NAME%"
echo.
echo 3. Check service status:
echo    sc query "%SERVICE_NAME%"
echo.
echo 4. View logs:
echo    type "%AGENT_DIR%\agent.log"
echo.

pause
