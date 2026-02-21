# ServerWatch Django Backend Automation Script
# This script monitors the Django server and restarts it if it's not running.

$serverHost = "0.0.0.0"
$serverPort = "8001"
$venvPath = ".\.venv\Scripts\python.exe"

if (!(Test-Path $venvPath)) {
    Write-Host "❌ Virtual environment not found at $venvPath. Checking for local python..." -ForegroundColor Red
    $pythonCmd = "python"
} else {
    $pythonCmd = $venvPath
}

Write-Host "🚀 Starting ServerWatch Django Backend Automation..." -ForegroundColor Cyan
Write-Host "📊 Monitoring port $serverPort..."

while ($true) {
    # Check if a process is listening on the port
    $processOnPort = Get-NetTCPConnection -LocalPort $serverPort -ErrorAction SilentlyContinue | Select-Object -First 1
    
    if ($null -eq $processOnPort) {
        Write-Host "$(Get-Date): ❌ Server not running on port $serverPort. Restarting..." -ForegroundColor Yellow
        Start-Process $pythonCmd -ArgumentList "manage.py runserver $serverHost`:$serverPort" -NoNewWindow
        
        # Wait for server to start
        Start-Sleep -Seconds 10
    } else {
        # Server is running, wait before checking again
        Start-Sleep -Seconds 30
    }
}
