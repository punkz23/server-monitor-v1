# Django Server Management PowerShell Script
# Automatically starts Django server and backend services
# Author: ServerWatch Monitoring System
# Version: 1.0

param(
    [Parameter(Mandatory=$false)]
    [string]$ProjectPath = "C:\Users\igibo\CascadeProjects\django-serverwatch",
    
    [Parameter(Mandatory=$false)]
    [string]$VirtualEnvPath = "C:\Users\igibo\CascadeProjects\django-serverwatch\venv",
    
    [Parameter(Mandatory=$false)]
    [string]$PythonExe = "python",
    
    [Parameter(Mandatory=$false)]
    [int]$ServerPort = 8000,
    
    [Parameter(Mandatory=$false)]
    [string]$LogLevel = "INFO",
    
    [Parameter(Mandatory=$false)]
    [switch]$AutoRestart = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$CreateService = $false,
    
    [Parameter(Mandatory=$false)]
    [string]$ServiceName = "DjangoServerWatch"
)

# Color output functions
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    
    $colors = @{
        "INFO" = "Green";
        "SUCCESS" = "Green"; 
        "WARNING" = "Yellow";
        "ERROR" = "Red";
        "DEBUG" = "Cyan";
        "HEADER" = "Magenta"
    }
    
    $color = $colors[$Level]
    if ($color) {
        Write-Host $Message -ForegroundColor $color
    } else {
        Write-Host $Message
    }
}

function Write-Header {
    param([string]$Message)
    Write-ColorOutput -Message $Message -Level "HEADER"
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput -Message $Message -Level "SUCCESS"
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput -Message $Message -Level "WARNING"
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput -Message $Message -Level "ERROR"
}

function Write-Info {
    param([string]$Message)
    Write-ColorOutput -Message $Message -Level "INFO"
}

function Write-Debug {
    param([string]$Message)
    Write-ColorOutput -Message $Message -Level "DEBUG"
}

# Check if running as Administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        return $true
    }
    return $false
}

# Check if port is available
function Test-PortAvailable {
    param([int]$Port)
    
    try {
        $listener = [System.Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().GetTcpIPProperties().GetActiveTcpListeners()
        $inUse = $listener | Where-Object { $_.LocalPort -eq $Port }
        return -not $inUse
    }
    catch {
        return $true
    }
}

# Start Django development server
function Start-DjangoServer {
    Write-Header "🚀 Starting Django Server"
    Write-Info "Project Path: $ProjectPath"
    Write-Info "Server Port: $ServerPort"
    Write-Info "Log Level: $LogLevel"
    
    # Check if project directory exists
    if (-not (Test-Path $ProjectPath)) {
        Write-Error "Project directory not found: $ProjectPath"
        return $false
    }
    
    # Check if Python executable exists
    $pythonPath = Get-Command $PythonExe -ErrorAction SilentlyContinue
    if (-not $pythonPath) {
        Write-Error "Python executable not found: $PythonExe"
        return $false
    }
    
    # Change to project directory
    Set-Location $ProjectPath
    
    # Check if virtual environment exists
    if (Test-Path $VirtualEnvPath) {
        Write-Info "Activating virtual environment..."
        $activateScript = Join-Path $VirtualEnvPath "Scripts\Activate.ps1"
        if (Test-Path $activateScript) {
            & $activateScript
            Write-Success "Virtual environment activated"
        } else {
            Write-Warning "Virtual environment activation script not found, continuing without venv..."
        }
    }
    
    # Set environment variables
    $env:DJANGO_SETTINGS_MODULE = "serverwatch.settings"
    $env:PYTHONPATH = $ProjectPath
    $env:PATHEXT = ".PY"
    
    # Check if port is available
    if (-not (Test-PortAvailable $ServerPort)) {
        Write-Warning "Port $ServerPort might be in use. Attempting to start anyway..."
    }
    
    # Start Django server
    try {
        Write-Info "Starting Django development server on port $ServerPort..."
        $serverArgs = @("manage.py", "runserver", "0.0.0.0:$ServerPort", "--noreload")
        
        # Start the server process
        $serverProcess = Start-Process -FilePath $pythonPath.Path -ArgumentList $serverArgs -WorkingDirectory $ProjectPath -PassThru
        
        if ($serverProcess) {
            Write-Success "✅ Django server started successfully!"
            Write-Info "Process ID: $($serverProcess.Id)"
            Write-Info "Server URL: http://localhost:$ServerPort"
            Write-Info "Dashboard URL: http://localhost:$ServerPort/monitoring/"
            Write-Info "Press Ctrl+C to stop the server"
            
            # Save process info to file for monitoring
            $processInfo = @{
                "ProcessId" = $serverProcess.Id;
                "StartTime" = Get-Date;
                "Port" = $ServerPort;
                "ProjectPath" = $ProjectPath;
                "PythonPath" = $pythonPath.Path
            }
            $processInfo | ConvertTo-Json | Out-File -FilePath ".\django_server_info.json" -Encoding UTF8
            
            return $serverProcess
        } else {
            Write-Error "Failed to start Django server"
            return $false
        }
    }
    catch {
        Write-Error "Error starting Django server: $($_.Exception.Message)"
        return $false
    }
}

# Stop Django server
function Stop-DjangoServer {
    Write-Header "🛑 Stopping Django Server"
    
    # Try to read server info from file
    $serverInfoFile = Join-Path $ProjectPath "\django_server_info.json"
    
    if (Test-Path $serverInfoFile) {
        try {
            $serverInfo = Get-Content $serverInfoFile -Raw | ConvertFrom-Json
            $processId = $serverInfo.ProcessId
            
            if ($processId) {
                Write-Info "Found running Django server process: $processId"
                
                # Try to stop the process gracefully
                $serverProcess = Get-Process -Id $processId -ErrorAction SilentlyContinue
                
                if ($serverProcess) {
                    Write-Info "Stopping Django server process..."
                    $serverProcess.Kill()
                    
                    # Wait for process to end
                    $timeout = 30
                    $stopped = $false
                    
                    for ($i = 0; $i -lt $timeout; $i++) {
                        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
                        if (-not $process) {
                            $stopped = $true
                            break
                        }
                        Start-Sleep -Seconds 1
                    }
                    
                    if ($stopped) {
                        Write-Success "✅ Django server stopped successfully"
                        Remove-Item $serverInfoFile -Force
                    } else {
                        Write-Warning "Server process did not stop gracefully within $timeout seconds"
                        Write-Warning "You may need to manually kill the process"
                    }
                } else {
                    Write-Warning "Server process not found, may already be stopped"
                }
            }
        }
        catch {
            Write-Error "Error reading server info: $($_.Exception.Message)"
        }
    }
    else {
        Write-Info "No running Django server found"
    }
}

# Check server status
function Get-DjangoServerStatus {
    Write-Header "📊 Django Server Status"
    
    $serverInfoFile = Join-Path $ProjectPath "\django_server_info.json"
    
    if (Test-Path $serverInfoFile) {
        try {
            $serverInfo = Get-Content $serverInfoFile -Raw | ConvertFrom-Json
            $processId = $serverInfo.ProcessId
            
            if ($processId) {
                $serverProcess = Get-Process -Id $processId -ErrorAction SilentlyContinue
                
                if ($serverProcess) {
                    $startTime = [DateTime]$serverInfo.StartTime
                    $runningTime = (Get-Date) - $startTime
                    Write-Success "✅ Django server is RUNNING"
                    Write-Info "Process ID: $processId"
                    Write-Info "Running for: $($runningTime.Hours) hours, $($runningTime.Minutes) minutes"
                    Write-Info "Server URL: http://localhost:$($serverInfo.Port)"
                    Write-Info "Dashboard: http://localhost:$($serverInfo.Port)/monitoring/"
                    return $true
                } else {
                    Write-Warning "Server process found but not running"
                    return $false
                }
            } else {
                Write-Info "No server information available"
                return $false
            }
        }
        catch {
            Write-Error "Error checking server status: $($_.Exception.Message)"
            return $false
        }
    }
    else {
        Write-Info "No Django server is currently running"
        return $false
    }
}

# Create Windows Service
function Create-WindowsService {
    Write-Header "🔧 Creating Windows Service"
    
    if (-not (Test-Administrator)) {
        Write-Error "Administrator privileges required to create Windows service"
        return $false
    }
    
    $serviceScript = @"
# Django Server Watch Service
# Generated by PowerShell script

`$ServiceName = "$ServiceName"
`$ProjectPath = "$ProjectPath"
`$PythonExe = "$PythonExe"
`$ServerPort = $ServerPort"

# Service main function
function Main-Service {
    # Change to project directory
    cd `$ProjectPath
    
    # Activate virtual environment if exists
    if (Test-Path `$VirtualEnvPath) {
        `$VirtualEnvPath\Scripts\Activate.ps1
    }
    
    # Set environment variables
    `$env:DJANGO_SETTINGS_MODULE = "serverwatch.settings"
    `$env:PYTHONPATH = `$ProjectPath
    
    # Start Django server
    `$PythonExe manage.py runserver 0.0.0.0:`$ServerPort --noreload
}

# Service installation
function Install-Service {
    param(`$serviceName)
    
    # Create service executable script
    `$serviceScriptPath = "C:\Program Files\DjangoServerWatch\service.ps1"
    `$serviceScript = @"
# Django Server Watch Service
`$serviceName = "$serviceName"

`$serviceScriptPath = "$serviceScriptPath"

# Service main function
function Main-Service {
    # Change to project directory
    cd `$ProjectPath
    
    # Activate virtual environment if exists
    if (Test-Path `$VirtualEnvPath) {
        `$VirtualEnvPath\Scripts\Activate.ps1
    }
    
    # Set environment variables
    `$env:DJANGO_SETTINGS_MODULE = "serverwatch.settings"
    `$env:PYTHONPATH = `$ProjectPath
    
    # Start Django server
    `$PythonExe manage.py runserver 0.0.0.0:`$ServerPort --noreload
}

# Install the service
New-Service -Name `$serviceName -DisplayName "Django Server Watch" -Description "Automatically starts Django server and backend" -BinaryPathName PowerShell.exe -StartupType Automatic -ServiceType Win32OwnProcess -ErrorAction Continue
"@
    
    # Create service directory if not exists
    $serviceDir = Split-Path $serviceScriptPath -Parent
    if (-not (Test-Path $serviceDir)) {
        New-Item -ItemType Directory -Path $serviceDir -Force
    }
    
    # Save service script
    $serviceScript | Out-File -FilePath $serviceScriptPath -Encoding UTF8
    
    # Install the service
    try {
        New-Service -Name $serviceName -DisplayName "Django Server Watch" -Description "Automatically starts Django server and backend" -BinaryPathName "powershell.exe" -StartupType Automatic -ServiceType Win32OwnProcess -ErrorAction Continue
        
        Write-Success "✅ Windows service '$serviceName' created successfully"
        Write-Info "Service will start Django server automatically on system boot"
        Write-Info "To manage service: Get-Service `$serviceName | Start-Service `$serviceName | Stop-Service `$serviceName | Remove-Service `$serviceName"
        
        return $true
    }
    catch {
        Write-Error "Failed to create Windows service: $($_.Exception.Message)"
        return $false
    }
}

# Main execution logic
function Main {
    Write-Header "🎯 Django Server Management Script"
    Write-Info "Project Path: $ProjectPath"
    Write-Info "Server Port: $ServerPort"
    Write-Info "Log Level: $LogLevel"
    Write-Info "Auto Restart: $AutoRestart"
    
    # Check administrator privileges
    if (-not (Test-Administrator)) {
        Write-Warning "Some operations require administrator privileges"
    }
    
    # Create service if requested
    if ($CreateService) {
        Create-WindowsService
        return
    }
    
    # Stop existing server if running
    Stop-DjangoServer
    
    # Start new server
    $serverProcess = Start-DjangoServer
    
    if ($serverProcess) {
        Write-Success "🎉 Django server started successfully!"
        Write-Info ""
        Write-Info "📱 Server running at: http://localhost:$ServerPort"
        Write-Info "📊 Dashboard available at: http://localhost:$ServerPort/monitoring/"
        Write-Info "🔄 API endpoints available at: http://localhost:$ServerPort/api/"
        Write-Info ""
        Write-Info "💡 Management Commands:"
        Write-Info "   Stop server: .\django_server.ps1 Stop"
        Write-Info "   Check status: .\django_server.ps1 Status"
        Write-Info "   Restart server: .\django_server.ps1 Restart"
        Write-Info "   Start server: .\django_server.ps1 Start"
        Write-Info ""
        Write-Info "💡 To stop server: Press Ctrl+C in this terminal"
        Write-Info "💡 Server info saved to: .\django_server_info.json"
        
        if ($AutoRestart) {
            Write-Info "🔄 Auto-restart enabled - server will restart on crashes"
        }
        
        # Keep script running and monitor server
        try {
            while ($true) {
                Start-Sleep -Seconds 30
                
                # Check if server is still running
                $serverProcess = Get-Process -Id $serverProcess.Id -ErrorAction SilentlyContinue
                
                if (-not $serverProcess) {
                    Write-Warning "⚠️ Django server process stopped unexpectedly"
                    
                    if ($AutoRestart) {
                        Write-Info "🔄 Auto-restarting Django server..."
                        $serverProcess = Start-DjangoServer
                        
                        if ($serverProcess) {
                            Write-Success "✅ Django server restarted successfully"
                        } else {
                            Write-Error "❌ Failed to restart Django server"
                            break
                        }
                    } else {
                        Write-Warning "❌ Django server stopped and auto-restart is disabled"
                        break
                    }
                }
                
                # Check for user input to stop
                if ($Host.UI.RawUI.KeyAvailable -and $Host.UI.RawUI.ReadKeyAvailable()) {
                    $key = $Host.UI.RawUI.ReadKey(100)
                    if ($key.Character -eq "q" -or $key.Character -eq "Q") {
                        Write-Info "🛑 Stopping Django server..."
                        Stop-DjangoServer
                        break
                    }
                }
            }
        }
        catch {
            Write-Error "Server monitoring error: $($_.Exception.Message)"
        }
        finally {
            # Cleanup on exit
            Stop-DjangoServer
            Write-Info "🧹 Django server stopped and cleaned up"
        }
    }
    else {
        Write-Error "❌ Failed to start Django server"
    }
}

# Command line interface
function Show-Help {
    Write-Header "📖 Django Server Management - Help"
    Write-Info ""
    Write-Info "Usage: .\django_server.ps1 [Command] [Parameters]"
    Write-Info ""
    Write-Info "Commands:"
    Write-Info "  Start              Start Django server and backend"
    Write-Info "  Stop               Stop running Django server"
    Write-Info "  Restart            Restart Django server"
    Write-Info "  Status             Check Django server status"
    Write-Info "  Install            Install as Windows service"
    Write-Info ""
    Write-Info "Parameters:"
    Write-Info "  -ProjectPath <path>     Project directory path"
    Write-Info "  -VirtualEnvPath <path>   Virtual environment path"
    Write-Info "  -PythonExe <path>        Python executable path"
    Write-Info "  -ServerPort <port>       Server port (default: 8000)"
    Write-Info "  -LogLevel <level>        Log level (INFO, SUCCESS, WARNING, ERROR, DEBUG)"
    Write-Info "  -AutoRestart            Enable auto-restart on crashes"
    Write-Info "  -CreateService         Install as Windows service"
    Write-Info ""
    Write-Info "Examples:"
    Write-Info "  .\django_server.ps1 Start"
    Write-Info "  .\django_server.ps1 Start -ProjectPath `"C:\MyProject`" -ServerPort 8080"
    Write-Info "  .\django_server.ps1 Install -CreateService"
}

# Process command line arguments
switch ($args[0]) {
    "Start" {
        Main
    }
    "Stop" {
        Stop-DjangoServer
    }
    "Restart" {
        Stop-DjangoServer
        Start-Sleep -Seconds 2
        Start-DjangoServer
    }
    "Status" {
        Get-DjangoServerStatus
    }
    "Install" {
        Create-WindowsService
    }
    "Help" {
        Show-Help
    }
    default {
        Write-Error "Unknown command: $($args[0])"
        Show-Help
    }
}
