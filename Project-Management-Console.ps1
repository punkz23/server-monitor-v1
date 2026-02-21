# ASCII-Compatible PowerShell Project Management Console
# Works on all systems without special characters

# Project configuration
$projects = @{
    "new_online_website" = @{
        Name = "New Online Website"
        RepoUrl = "github.com/rsdaroy/new_online_website.git"
        Servers = @{
            "1" = @{ Hostname = "192.168.254.13"; User = "w4-assistant"; Password = "O6G1Amvos0icqGRC"; Path = "/var/www/new_online_website" }
            "2" = @{ Hostname = "192.168.253.15"; User = "w1-assistant"; Password = "hIkLM#X5x1sjwIrM"; Path = "/var/www/new_online_website" }
        }
    }
    "new_track_and_trace" = @{
        Name = "New Track and Trace"
        RepoUrl = "github.com/rsdaroy/new_track_and_trace.git"
        Servers = @{
            "1" = @{ Hostname = "192.168.254.13"; User = "w4-assistant"; Password = "O6G1Amvos0icqGRC"; Path = "/var/www/new_track_and_trace" }
        }
    }
    "new_supplier" = @{
        Name = "New Supplier"
        RepoUrl = "github.com/rsdaroy/new_supplier.git"
        Servers = @{
            "1" = @{ Hostname = "192.168.254.13"; User = "w4-assistant"; Password = "O6G1Amvos0icqGRC"; Path = "/var/www/new_supplier" }
        }
    }
    "career.dailyoverland" = @{
        Name = "Career Dailyoverland"
        RepoUrl = "github.com/rsdaroy/career.dailyoverland.git"
        Servers = @{
            "1" = @{ Hostname = "192.168.254.13"; User = "w4-assistant"; Password = "O6G1Amvos0icqGRC"; Path = "/var/www/career.dailyoverland" }
        }
    }
    "management" = @{
        Name = "Management"
        RepoUrl = "github.com/rsdaroy/management.git"
        Servers = @{
            "1" = @{ Hostname = "192.168.254.7"; User = "hp44k6q2-assistant"; Password = "Jed9TIYYlwHWl5eu"; Path = "/var/www/html/management" }
            "2" = @{ Hostname = "192.168.253.7"; User = "ho-w1-assistant"; Password = "PB7hS5jNEhLxvjZN"; Path = "/var/www/html/management" }
        }
    }
    "doffsystem" = @{
        Name = "DOFF System"
        RepoUrl = "github.com/rsdaroy/doffsystem.git"
        Servers = @{
            "1" = @{ Hostname = "192.168.254.7"; User = "hp44k6q2-assistant"; Password = "Jed9TIYYlwHWl5eu"; Path = "/var/www/html/doffsystem" }
            "2" = @{ Hostname = "192.168.253.7"; User = "ho-w1-assistant"; Password = "PB7hS5jNEhLxvjZN"; Path = "/var/www/html/doffsystem" }
        }
    }
    "fuelhub" = @{
        Name = "Fuel Hub"
        RepoUrl = "github.com/rsdaroy/fuelhub.git"
        Servers = @{
            "1" = @{ Hostname = "192.168.254.7"; User = "hp44k6q2-assistant"; Password = "Jed9TIYYlwHWl5eu"; Path = "/var/www/html/fuelhub" }
            "2" = @{ Hostname = "192.168.253.7"; User = "ho-w1-assistant"; Password = "PB7hS5jNEhLxvjZN"; Path = "/var/www/html/fuelhub" }
        }
    }
    "new_employee" = @{
        Name = "New Employee"
        RepoUrl = "github.com/rsdaroy/new_employee.git"
        Servers = @{
            "1" = @{ Hostname = "192.168.254.50"; User = "ws3-assistant"; Password = '6c$7TpzjzYpTpbDp'; Path = "/var/www/new_employee" }
            "2" = @{ Hostname = "192.168.253.15"; User = "w1-assistant"; Password = "hIkLM#X5x1sjwIrM"; Path = "/var/www/new_employee" }
        }
    }
    "new_doff" = @{
        Name = "New DOFF"
        RepoUrl = "github.com/rsdaroy/new_doff.git"
        Servers = @{
            "1" = @{ Hostname = "192.168.254.50"; User = "ws3-assistant"; Password = '6c$7TpzjzYpTpbDp'; Path = "/var/www/new_doff" }
            "2" = @{ Hostname = "192.168.253.15"; User = "w1-assistant"; Password = "hIkLM#X5x1sjwIrM"; Path = "/var/www/new_doff" }
        }
    }
    "doff_dtr" = @{
        Name = "DOFF DTR"
        RepoUrl = "github.com/rsdaroy/doff_dtr.git"
        Servers = @{
            "1" = @{ Hostname = "192.168.254.50"; User = "ws3-assistant"; Password = '6c$7TpzjzYpTpbDp'; Path = "/var/www/doff_dtr" }
            "2" = @{ Hostname = "192.168.253.15"; User = "w1-assistant"; Password = "hIkLM#X5x1sjwIrM"; Path = "/var/www/doff_dtr" }
        }
    }
    "api" = @{
        Name = "API"
        RepoUrl = "github.com/rsdaroy/api.git"
        Servers = @{
            "1" = @{ Hostname = "192.168.254.50"; User = "ws3-assistant"; Password = '6c$7TpzjzYpTpbDp'; Path = "/var/www/api" }
        }
    }
    "digital_id" = @{
        Name = "Digital ID"
        RepoUrl = "github.com/rsdaroy/digital_id.git"
        Servers = @{
            "1" = @{ Hostname = "192.168.254.50"; User = "ws3-assistant"; Password = '6c$7TpzjzYpTpbDp'; Path = "/var/www/digital_id" }
        }
    }
}

# ASCII logging function
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $symbol = switch($Level) {
        "SUCCESS" { "[OK]" }
        "WARNING" { "[!]" }
        "ERROR"   { "[X]" }
        default   { "[i]" }
    }
    
    $color = switch($Level) {
        "SUCCESS" { "Green" }
        "WARNING" { "Yellow" }
        "ERROR"   { "Red" }
        default   { "Cyan" }
    }
    
    $logEntry = "[$timestamp] $symbol $Message"
    Write-Host $logEntry -ForegroundColor $color
}

# Menu system
function Show-Menu {
    param([string]$Title, [hashtable]$Options)
    
    Clear-Host
    Write-Host "===== $Title =====" -ForegroundColor Magenta
    
    $keys = $Options.Keys | Sort-Object
    foreach ($key in $keys) {
        Write-Host "$key. $($Options[$key])" -ForegroundColor Yellow
    }
    
    $selection = Read-Host "`nPlease select an option (1-$($keys.Count))"
    return $selection
}

function Normalize-Text {
    param([object]$Value)
    $s = ""
    if ($null -ne $Value) {
        try { $s = [string]$Value } catch { $s = "" }
    }
    if ($null -eq $s) { $s = "" }
    return $s.Trim()
}

$githubToken = $env:GITHUB_TOKEN

function Ensure-Prereqs {
    if (-not (Get-Command plink -ErrorAction SilentlyContinue)) {
        Write-Log "plink.exe not found in PATH. Install PuTTY or add plink to PATH." "ERROR"
        return $false
    }
    if ([string]::IsNullOrWhiteSpace($githubToken)) {
        $script:githubToken = Read-Host "Enter GitHub token (will not be saved)"
    }
    if ([string]::IsNullOrWhiteSpace($githubToken)) {
        Write-Log "GitHub token is required." "ERROR"
        return $false
    }
    return $true
}

function Invoke-Remote {
    param(
        [hashtable]$Server,
        [string]$Command,
        [int]$TimeoutSeconds = 60
    )

    $hostname = $Server.Hostname
    $user = $Server.User
    $pass = $Server.Password
    $hostKey = $Server.HostKey

    $outFile = [System.IO.Path]::GetTempFileName()
    $errFile = [System.IO.Path]::GetTempFileName()
    try {
        $args = @("-ssh", "-batch", "-no-antispoof", "-T")
        if (-not [string]::IsNullOrWhiteSpace($hostKey)) {
            $args += @("-hostkey", $hostKey)
        }
        $args += @("$user@$hostname", "-pw", $pass, $Command)
        $p = Start-Process -FilePath "plink" -ArgumentList $args -RedirectStandardOutput $outFile -RedirectStandardError $errFile -PassThru -NoNewWindow
        $done = $p.WaitForExit($TimeoutSeconds * 1000)
        if (-not $done) {
            $p.Kill()
            return [pscustomobject]@{ TimedOut = $true; ExitCode = $null; StdOut = ""; StdErr = "Timed out" }
        }
        $stdout = ""
        $stderr = ""
        if (Test-Path $outFile) { $stdout = Get-Content $outFile -Raw }
        if (Test-Path $errFile) { $stderr = Get-Content $errFile -Raw }
        return [pscustomobject]@{ TimedOut = $false; ExitCode = $p.ExitCode; StdOut = $stdout; StdErr = $stderr }
    }
    catch {
        return [pscustomobject]@{ TimedOut = $false; ExitCode = $null; StdOut = ""; StdErr = "$_" }
    }
    finally {
        Remove-Item $outFile, $errFile -ErrorAction SilentlyContinue
    }
}

function Invoke-RemoteWithRetry {
    param(
        [hashtable]$Server,
        [string]$Command,
        [int]$TimeoutSeconds,
        [int]$MaxAttempts = 2
    )

    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        $r = Invoke-Remote -Server $Server -Command $Command -TimeoutSeconds $TimeoutSeconds
        if (-not $r) { return $r }

        $stderr = Normalize-Text $r.StdErr
        if ($stderr -match "(?i)access denied|configured password was not accepted") {
            if ($attempt -ge $MaxAttempts) { return $r }

            Write-Log "SSH password rejected for $($Server.User)@$($Server.Hostname)." "WARNING"
            $retry = Read-Host "Re-enter password and retry on $($Server.Hostname)? (y/n)"
            if ($retry -notmatch '^(?i)y') { return $r }

            $newPass = Read-Host "Enter password for $($Server.User)@$($Server.Hostname) (will not be saved)"
            if (-not [string]::IsNullOrWhiteSpace($newPass)) {
                $Server.Password = $newPass
            }

            Start-Sleep -Seconds 1
            continue
        }
        if ($stderr -match "(?i)could not resolve host:\s*github\.com") {
            if ($attempt -ge $MaxAttempts) { return $r }

            Write-Log "Network issue on $($Server.Hostname): $stderr" "WARNING"
            $retry = Read-Host "Retry on $($Server.Hostname)? (y/n)"
            if ($retry -notmatch '^(?i)y') { return $r }

            Start-Sleep -Seconds 2
            continue
        }

        return $r
    }

    return $null
}

function Select-Project {
    $ordered = $projects.Keys | Sort-Object { $projects[$_].Name }
    Write-Host ""; Write-Host "Available Projects:" -ForegroundColor Green
    for ($i = 0; $i -lt $ordered.Count; $i++) {
        $p = $projects[$ordered[$i]]
        Write-Host "  $($i + 1). $($p.Name)  (servers: $($p.Servers.Count))" -ForegroundColor Yellow
    }
    $raw = Read-Host "Select project number (1-$($ordered.Count))"
    $n = 0
    if (-not [int]::TryParse($raw, [ref]$n)) { return $null }
    if ($n -lt 1 -or $n -gt $ordered.Count) { return $null }
    return $ordered[$n - 1]
}

function Select-TargetsForProject {
    param([hashtable]$Project)

    $serverKeys = $Project.Servers.Keys | Sort-Object
    if ($serverKeys.Count -eq 1) {
        return @($Project.Servers[$serverKeys[0]])
    }

    Write-Host ""; Write-Host "Where do you want to run this project?" -ForegroundColor Green
    Write-Host "  1. All servers" -ForegroundColor Yellow
    for ($i = 0; $i -lt $serverKeys.Count; $i++) {
        $s = $Project.Servers[$serverKeys[$i]]
        Write-Host "  $($i + 2). $($s.Hostname)  ($($s.Path))" -ForegroundColor Yellow
    }

    $raw = Read-Host "Select option (1-$($serverKeys.Count + 1))"
    $n = 0
    if (-not [int]::TryParse($raw, [ref]$n)) { return $null }

    if ($n -eq 1) {
        $targets = @()
        foreach ($k in $serverKeys) { $targets += $Project.Servers[$k] }
        return $targets
    }

    $idx = $n - 2
    if ($idx -lt 0 -or $idx -ge $serverKeys.Count) { return $null }
    return @($Project.Servers[$serverKeys[$idx]])
}

function Run-GitPull {
    param([hashtable]$Project, [hashtable[]]$Targets)

    $ok = 0
    $total = $Targets.Count
    foreach ($t in $Targets) {
        Write-Log "Git pull on $($t.Hostname) ($($t.Path))" "INFO"
        $cmd = "cd $($t.Path)`ngit pull https://$githubToken@$($Project.RepoUrl)"
        $r = Invoke-RemoteWithRetry -Server $t -Command $cmd -TimeoutSeconds 120 -MaxAttempts 2
        if (-not $r) {
            Write-Log "Failed to execute SSH command on $($t.Hostname)" "ERROR"
            continue
        }
        if ($r.TimedOut) {
            Write-Log "Timed out on $($t.Hostname)" "ERROR"
            continue
        }
        $stdout = Normalize-Text $r.StdOut
        $stderr = Normalize-Text $r.StdErr

        if (-not [string]::IsNullOrWhiteSpace($stderr)) {
            if ($stderr -match "(?i)cannot confirm a host key in batch mode") {
                Write-Log "Host key not cached for $($t.Hostname). Run: plink -ssh $($t.User)@$($t.Hostname) then type y to cache the key." "ERROR"
                continue
            }
            if ($stderr -match "(?i)could not resolve host:\s*github\.com") {
                Write-Log "Network issue on $($t.Hostname): $stderr" "ERROR"
                continue
            }
            if ($stderr -match "(?i)fatal|permission denied|connection refused") {
                Write-Log "Error on $($t.Hostname): $stderr" "ERROR"
                continue
            }
            if ($stderr -match "(?i)error") {
                Write-Log "Error on $($t.Hostname): $stderr" "ERROR"
                continue
            }
            Write-Log $stderr "INFO"
        }

        $looksSuccessful = $false
        if (-not [string]::IsNullOrWhiteSpace($stdout)) {
            if ($stdout -match "Already up to date|Fast-forward|Updating|files changed") {
                $looksSuccessful = $true
            }
        }
        if ($r.ExitCode -eq 0) { $looksSuccessful = $true }

        if ($looksSuccessful) {
            if (-not [string]::IsNullOrWhiteSpace($stdout)) {
                Write-Log "OK on $($t.Hostname): $stdout" "SUCCESS"
            } else {
                Write-Log "OK on $($t.Hostname)" "SUCCESS"
            }
            $ok++
        } else {
            if (-not [string]::IsNullOrWhiteSpace($stdout)) {
                Write-Log "Git pull may have failed on $($t.Hostname): $stdout" "ERROR"
            } else {
                Write-Log "Git pull may have failed on $($t.Hostname)" "ERROR"
            }
        }
    }
    Write-Log "Git pull completed: $ok/$total" "SUCCESS"
}

function Run-CustomCommand {
    param([hashtable[]]$Targets)

    $cmdInput = Read-Host "Enter command to run on remote server(s)"
    if ([string]::IsNullOrWhiteSpace($cmdInput)) { return }

    foreach ($t in $Targets) {
        Write-Log "Running on $($t.Hostname): $cmdInput" "INFO"
        $cmd = "cd $($t.Path) && $cmdInput"
        $r = Invoke-RemoteWithRetry -Server $t -Command $cmd -TimeoutSeconds 300 -MaxAttempts 2
        if (-not $r) {
            Write-Log "Failed to execute SSH command on $($t.Hostname)" "ERROR"
            continue
        }
        if ($r.TimedOut) {
            Write-Log "Timed out on $($t.Hostname)" "ERROR"
            continue
        }
        $stdout = Normalize-Text $r.StdOut
        $stderr = Normalize-Text $r.StdErr

        if (-not [string]::IsNullOrWhiteSpace($stderr)) {
            if ($stderr -match "(?i)cannot confirm a host key in batch mode") {
                Write-Log "Host key not cached for $($t.Hostname). Run: plink -ssh $($t.User)@$($t.Hostname) then type y to cache the key." "ERROR"
                continue
            }
            if ($stderr -match "(?i)fatal|permission denied|connection refused|could not resolve host") {
                Write-Log "Error on $($t.Hostname): $stderr" "ERROR"
                continue
            }
            if ($stderr -match "(?i)error") {
                Write-Log "Error on $($t.Hostname): $stderr" "ERROR"
                continue
            }
            Write-Log $stderr "INFO"
        }

        if (-not [string]::IsNullOrWhiteSpace($stdout)) {
            Write-Host "----- $($t.Hostname) output -----" -ForegroundColor DarkGray
            Write-Host $stdout
        }
        if ($r.ExitCode -eq 0) {
            Write-Log "Done on $($t.Hostname)" "SUCCESS"
        } else {
            Write-Log "Command failed on $($t.Hostname)" "ERROR"
        }
    }
}

# Main execution
if (-not (Ensure-Prereqs)) { exit 1 }

$currentProjectKey = $null
$currentTargets = @()

:main while ($true) {
    $header = "Project Management Console"
    if ($currentProjectKey) {
        $p = $projects[$currentProjectKey]
        $header = "$header - Selected: $($p.Name)"
    }
    
    $menu = @{
        "1" = "Select Project"
        "2" = "Select Target Server(s)"
        "3" = "Run Git Pull"
        "4" = "Run Custom Command"
        "5" = "Show Current Selection"
        "6" = "Exit"
    }

    $choice = Show-Menu -Title $header -Options $menu

    switch ($choice) {
        "1" {
            $picked = Select-Project
            if (-not $picked) { Write-Log "Invalid project selection" "ERROR"; Start-Sleep 1; break }
            $currentProjectKey = $picked
            $currentTargets = @()
            $p = $projects[$currentProjectKey]
            Write-Log "Selected project: $($p.Name)" "SUCCESS"
            $currentTargets = Select-TargetsForProject -Project $p
            if (-not $currentTargets -or $currentTargets.Count -eq 0) {
                Write-Log "No targets selected" "WARNING"
            } else {
                Write-Log "Targets selected: $($currentTargets.Count)" "SUCCESS"
            }
            Read-Host "Press Enter to continue" | Out-Null
        }
        "2" {
            if (-not $currentProjectKey) { Write-Log "Select a project first" "WARNING"; Start-Sleep 1; break }
            $p = $projects[$currentProjectKey]
            $targets = Select-TargetsForProject -Project $p
            if (-not $targets) { Write-Log "Invalid target selection" "ERROR"; Start-Sleep 1; break }
            $currentTargets = $targets
            Write-Log "Targets updated: $($currentTargets.Count)" "SUCCESS"
            Read-Host "Press Enter to continue" | Out-Null
        }
        "3" {
            if (-not $currentProjectKey) { Write-Log "Select a project first" "WARNING"; Start-Sleep 1; break }
            if (-not $currentTargets -or $currentTargets.Count -eq 0) { Write-Log "Select target server(s) first" "WARNING"; Start-Sleep 1; break }
            $p = $projects[$currentProjectKey]
            Run-GitPull -Project $p -Targets $currentTargets
            Read-Host "Press Enter to continue" | Out-Null
        }
        "4" {
            if (-not $currentProjectKey) { Write-Log "Select a project first" "WARNING"; Start-Sleep 1; break }
            if (-not $currentTargets -or $currentTargets.Count -eq 0) { Write-Log "Select target server(s) first" "WARNING"; Start-Sleep 1; break }
            Run-CustomCommand -Targets $currentTargets
            Read-Host "Press Enter to continue" | Out-Null
        }
        "5" {
            Write-Host "" 
            if ($currentProjectKey) {
                $p = $projects[$currentProjectKey]
                Write-Host "Project: $($p.Name)" -ForegroundColor Green
                Write-Host "Repo:    $($p.RepoUrl)" -ForegroundColor Cyan
            } else {
                Write-Host "Project: (none)" -ForegroundColor Yellow
            }
            if ($currentTargets -and $currentTargets.Count -gt 0) {
                Write-Host "Targets:" -ForegroundColor Green
                foreach ($t in $currentTargets) {
                    Write-Host "  - $($t.Hostname)  $($t.Path)" -ForegroundColor Yellow
                }
            } else {
                Write-Host "Targets: (none)" -ForegroundColor Yellow
            }
            Read-Host "Press Enter to continue" | Out-Null
        }
        "6" {
            break main
        }
        default {
            Write-Log "Invalid selection" "ERROR"
            Start-Sleep 1
        }
    }
}
