@echo off
REM Daily SSL Certificate Check for ServerWatch
REM This script runs the daily certificate check and logs results

echo ========================================
echo Starting Daily SSL Certificate Check
echo Date: %date% %time%
echo ========================================

cd /d "C:\Users\igibo\CascadeProjects\django-serverwatch"

REM Run the daily certificate check
python manage.py daily_cert_check

REM Check the exit code
if %errorlevel% equ 0 (
    echo ✅ All certificates are healthy
) else if %errorlevel% equ 1 (
    echo ⚠️ Some certificates need attention soon
) else (
    echo 🚨 CRITICAL: Some certificates need immediate attention!
)

echo ========================================
echo Certificate check completed at %date% %time%
echo ========================================
pause
