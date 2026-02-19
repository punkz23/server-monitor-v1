@echo off
REM Automated Server Status Monitoring Script
REM This script starts the automated server monitoring service

echo ========================================
echo Server Status Monitoring Service
echo ========================================
echo.

cd /d "C:\Users\igibo\CascadeProjects\django-serverwatch"

echo Starting automated server monitoring...
python manage.py monitor_status start --interval 300

echo.
echo Monitoring service is now running!
echo Check interval: 5 minutes
echo.
echo To stop monitoring: python manage.py monitor_status stop
echo To check status: python manage.py monitor_status status
echo.
echo Press any key to exit...
pause > nul
