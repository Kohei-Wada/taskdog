# Taskdog Server - Windows Task Scheduler Uninstallation Script
# This script removes the taskdog-server scheduled task
#
# Usage: .\uninstall-service.ps1

$TaskName = "TaskdogServer"

Write-Host "Uninstalling Taskdog Server scheduled task..."

# Check if task exists
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if (-not $ExistingTask) {
    Write-Host "Scheduled task '$TaskName' not found. Nothing to uninstall."
    exit 0
}

# Stop the task if running
$TaskInfo = Get-ScheduledTaskInfo -TaskName $TaskName -ErrorAction SilentlyContinue
if ($TaskInfo -and $TaskInfo.LastTaskResult -eq 267009) {
    Write-Host "  Stopping running task..."
    Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
}

# Remove the task
try {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop
    Write-Host ""
    Write-Host "Taskdog Server uninstalled successfully!" -ForegroundColor Green
}
catch {
    Write-Error "Failed to remove scheduled task: $_"
    exit 1
}
