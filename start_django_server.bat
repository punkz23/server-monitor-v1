@echo off
REM Django Server Management Launcher
REM This script provides easy access to Django server management

setlocal enabledelayedexpansion

title Django Server Management

:menu
cls
echo.
echo  ========================================
echo    Django Server Management
echo  ========================================
echo.
echo    1. Start Django Server
echo    2. Stop Django Server  
echo    3. Restart Django Server
echo    4. Check Server Status
echo    5. Install Windows Service
echo    6. Exit
echo.
echo  ========================================
echo.

set /p choice="Select an option (1-6): "

if "%choice%"=="1" goto start
if "%choice%"=="2" goto stop
if "%choice%"=="3" goto restart  
if "%choice%"=="4" goto status
if "%choice%"=="5" goto install
if "%choice%"=="6" goto exit
goto menu

:start
cls
echo.
echo  🚀 Starting Django Server...
echo.
powershell.exe -ExecutionPolicy Bypass -File "django_server.ps1" Start
echo.
echo  Press any key to return to menu...
pause > nul
goto menu

:stop
cls
echo.
echo  🛑 Stopping Django Server...
echo.
powershell.exe -ExecutionPolicy Bypass -File "django_server.ps1" Stop
echo.
echo  Press any key to return to menu...
pause > nul
goto menu

:restart
cls
echo.
echo  🔄 Restarting Django Server...
echo.
powershell.exe -ExecutionPolicy Bypass -File "django_server.ps1" Restart
echo.
echo  Press any key to return to menu...
pause > nul
goto menu

:status
cls
echo.
echo  📊 Checking Django Server Status...
echo.
powershell.exe -ExecutionPolicy Bypass -File "django_server.ps1" Status
echo.
echo  Press any key to return to menu...
pause > nul
goto menu

:install
cls
echo.
echo  🔧 Installing Windows Service...
echo.
powershell.exe -ExecutionPolicy Bypass -File "django_server.ps1" Install
echo.
echo  Press any key to return to menu...
pause > nul
goto menu

:exit
cls
echo.
echo  👋 Exiting Django Server Management...
echo.
timeout /t 3 > nul
exit
