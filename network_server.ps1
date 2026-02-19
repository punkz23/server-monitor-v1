# Network-Enabled Django Server Script
param(
    [Parameter(Mandatory=$false)]
    [int]$Port = 8000,
    [Parameter(Mandatory=$false)]
    [switch]$ConfigureFirewall = $false
)

Write-Host "🌐 Starting Network-Enabled Django Server" -ForegroundColor Green
Write-Host "Port: $Port" -ForegroundColor Cyan

# Get local IP address
$localIP = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Ethernet*").IPAddress | Select-Object -First 1
if (-not $localIP) {
    $localIP = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Wi-Fi*").IPAddress | Select-Object -First 1
}

if ($localIP) {
    Write-Host "Local IP: $localIP" -ForegroundColor Yellow
    Write-Host "Access URLs:" -ForegroundColor White
    Write-Host "  Local:    http://localhost:$Port" -ForegroundColor Green
    Write-Host "  Network:  http://$localIP:$Port" -ForegroundColor Green
    Write-Host "  Dashboard: http://$localIP:$Port/monitoring/" -ForegroundColor Green
} else {
    Write-Host "Could not detect local IP" -ForegroundColor Yellow
    Write-Host "Access: http://localhost:$Port" -ForegroundColor Green
}

# Configure firewall if requested
if ($ConfigureFirewall) {
    Write-Host "🔥 Configuring Windows Firewall..." -ForegroundColor Yellow
    try {
        New-NetFirewallRule -DisplayName "Django Server Port $Port" -Direction Inbound -Protocol TCP -LocalPort $Port -Action Allow -ErrorAction SilentlyContinue
        Write-Host "✅ Firewall rule created" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ Firewall configuration failed - configure manually" -ForegroundColor Yellow
    }
}

# Change to project directory
Set-Location "C:\Users\igibo\CascadeProjects\django-serverwatch"

# Check if Django project exists
if (-not (Test-Path "manage.py")) {
    Write-Host "❌ ERROR: manage.py not found!" -ForegroundColor Red
    exit 1
}

# Start server
Write-Host "🚀 Starting network server..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "---" -ForegroundColor White

python manage.py runserver 0.0.0.0:$Port
