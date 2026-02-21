@echo off
setlocal

echo 🚀 Starting ServerWatch Django Backend Automation...

:: Check if PowerShell is available
where powershell >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ PowerShell not found. Cannot start automation script.
    pause
    exit /b 1
)

:: Run the PowerShell automation script
powershell -ExecutionPolicy Bypass -File .\django_server.ps1

pause
