@echo off
REM Setup Windows Task Scheduler for Automated Server Monitoring
REM This creates a scheduled task to run server monitoring automatically

echo ========================================
echo Setup Automated Server Monitoring
echo ========================================
echo.

cd /d "C:\Users\igibo\CascadeProjects\django-serverwatch"

echo Creating Windows Task Scheduler entry...
echo.

REM Remove existing task if it exists
schtasks /delete /tn "ServerStatusMonitoring" /f >nul 2>&1

REM Create new task to run monitoring every 5 minutes
schtasks /create /tn "ServerStatusMonitoring" /tr "C:\Users\igibo\CascadeProjects\django-serverwatch\monitor\management\commands\update_server_status.py" /sc minute /mo 5 /ru "SYSTEM" /f

if %ERRORLEVEL% EQU 0 (
    echo ✅ Task Scheduler entry created successfully!
    echo 📊 Monitoring will run every 5 minutes
    echo 🔧 Task name: ServerStatusMonitoring
    echo.
    echo To view the task: schtasks /query /tn "ServerStatusMonitoring"
    echo To delete the task: schtasks /delete /tn "ServerStatusMonitoring" /f
    echo To run manually: python manage.py update_server_status
) else (
    echo ❌ Failed to create Task Scheduler entry
    echo 💡 Try running as Administrator
)

echo.
echo Press any key to exit...
pause > nul
