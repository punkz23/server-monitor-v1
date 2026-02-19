# Simple Django Server Start Script
param(
    [Parameter(Mandatory=$false)]
    [int]$Port = 8000
)

Write-Host "Starting Django Server on Port $Port" -ForegroundColor Green

# Change to project directory
Set-Location "C:\Users\igibo\CascadeProjects\django-serverwatch"

# Check if Django project exists
if (-not (Test-Path "manage.py")) {
    Write-Host "ERROR: manage.py not found in current directory!" -ForegroundColor Red
    Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow
    exit 1
}

# Check Django installation
try {
    $djangoVersion = python -c "import django; print(django.get_version())"
    Write-Host "Django version: $djangoVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Django not installed!" -ForegroundColor Red
    exit 1
}

# Start server with visible output
Write-Host "Starting server..." -ForegroundColor Cyan
Write-Host "Server will be available at: http://localhost:$Port" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "---" -ForegroundColor White

python manage.py runserver 0.0.0.0:$Port
