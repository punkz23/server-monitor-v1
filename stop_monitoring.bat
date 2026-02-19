@echo off
REM Stop Automated Server Status Monitoring Script
REM This script stops the automated server monitoring service

echo ========================================
echo Stop Server Status Monitoring Service
echo ========================================
echo.

cd /d "C:\Users\igibo\CascadeProjects\django-serverwatch"

echo Stopping automated server monitoring...
python manage.py monitor_status stop

echo.
echo Monitoring service has been stopped!
echo.
echo Press any key to exit...
pause > nul
