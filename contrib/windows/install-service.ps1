# Taskdog Server - Windows Task Scheduler Installation Script
# This script creates a scheduled task to run taskdog-server on login
#
# Usage: .\install-service.ps1 [-Host <host>] [-Port <port>]
#
# Requirements:
# - PowerShell 5.1 or later
# - taskdog-server must be installed (uv tool install taskdog-server)

param(
    [ValidatePattern('^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$|^localhost$|^0\.0\.0\.0$')]
    [string]$Host = "127.0.0.1",

    [ValidateRange(1, 65535)]
    [int]$Port = 8000
)

$TaskName = "TaskdogServer"
$Description = "Taskdog API Server - Task management REST API"

# Find taskdog-server executable
$TaskdogServer = Get-Command "taskdog-server" -ErrorAction SilentlyContinue
if (-not $TaskdogServer) {
    Write-Error "taskdog-server not found in PATH. Please install with: uv tool install taskdog-server"
    exit 1
}

$ExecutablePath = $TaskdogServer.Source
$Arguments = "--host $Host --port $Port --workers 1"

Write-Host "Installing Taskdog Server as scheduled task..."
Write-Host "  Executable: $ExecutablePath"
Write-Host "  Arguments: $Arguments"

# Remove existing task if present
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($ExistingTask) {
    Write-Host "  Removing existing task..."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create the scheduled task
$Action = New-ScheduledTaskAction -Execute $ExecutablePath -Argument $Arguments
$Trigger = New-ScheduledTaskTrigger -AtLogon -User $env:USERNAME
$Settings = New-ScheduledTaskSettingsSet `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Days 365) `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries

$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Description $Description `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Principal $Principal `
        -ErrorAction Stop | Out-Null

    Write-Host ""
    Write-Host "Taskdog Server installed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "The server will start automatically on login."
    Write-Host "To start it now, run:"
    Write-Host "  Start-ScheduledTask -TaskName $TaskName"
    Write-Host ""
    Write-Host "To check status:"
    Write-Host "  Get-ScheduledTask -TaskName $TaskName"
    Write-Host ""
    Write-Host "API will be available at: http://${Host}:${Port}"
    Write-Host "API docs: http://${Host}:${Port}/docs"
}
catch {
    Write-Error "Failed to create scheduled task: $_"
    exit 1
}
