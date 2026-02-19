@echo off
REM Check Server Status Monitoring Script
REM This script shows the current status of the monitoring service

echo ========================================
echo Server Status Monitoring Service Status
echo ========================================
echo.

cd /d "C:\Users\igibo\CascadeProjects\django-serverwatch"

python manage.py monitor_status status

echo.
echo Press any key to exit...
pause > nul
