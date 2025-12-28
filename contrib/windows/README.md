# Taskdog on Windows

This directory contains scripts for running Taskdog on Windows.

## Installation

### Prerequisites

1. **Python 3.13+** - Download from [python.org](https://www.python.org/downloads/)
2. **uv** - Python package installer

   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

### Install Taskdog

```powershell
# Install taskdog CLI/TUI and server as global commands
uv tool install taskdog
uv tool install taskdog-server
```

### Verify Installation

```powershell
taskdog --help
taskdog-server --help
```

## Data Locations

Taskdog stores data in standard Windows locations:

| Data Type | Location |
|-----------|----------|
| Database | `%LOCALAPPDATA%\taskdog\tasks.db` |
| Notes | `%LOCALAPPDATA%\taskdog\notes\` |
| Config | `%LOCALAPPDATA%\taskdog\core.toml` |

You can override these with environment variables:

- `XDG_DATA_HOME` - Base directory for data
- `XDG_CONFIG_HOME` - Base directory for config

## Running the Server

### Manual Start

```powershell
# Start server on default port (8000)
taskdog-server

# Custom host and port
taskdog-server --host 0.0.0.0 --port 3000
```

### Auto-Start with Task Scheduler

Use the provided PowerShell scripts to configure automatic startup:

```powershell
# Install (run as your user, no admin required)
.\install-service.ps1

# With custom host/port
.\install-service.ps1 -Host 0.0.0.0 -Port 3000

# Uninstall
.\uninstall-service.ps1
```

### Managing the Scheduled Task

```powershell
# Check status
Get-ScheduledTask -TaskName "TaskdogServer"

# Start manually
Start-ScheduledTask -TaskName "TaskdogServer"

# Stop
Stop-ScheduledTask -TaskName "TaskdogServer"

# View task info
Get-ScheduledTaskInfo -TaskName "TaskdogServer"
```

## CLI/TUI Configuration

Create `%LOCALAPPDATA%\taskdog\cli.toml` to configure the CLI/TUI connection:

```toml
[api]
host = "127.0.0.1"
port = 8000
```

Or use environment variables:

```powershell
$env:TASKDOG_API_HOST = "127.0.0.1"
$env:TASKDOG_API_PORT = "8000"
```

## Using the TUI

The TUI works in Windows Terminal and PowerShell:

```powershell
taskdog tui
```

For best experience, use [Windows Terminal](https://aka.ms/terminal) which has full Unicode and color support.

## Known Limitations

1. **Editor**: The `note` command requires an editor. Set `$env:EDITOR` or install VS Code:

   ```powershell
   $env:EDITOR = "code --wait"
   ```

2. **Makefile**: The project's Makefile is designed for Unix. Use the commands directly:

   ```powershell
   # Instead of: make test
   cd packages/taskdog-core
   uv run pytest tests/ -v
   ```

## Troubleshooting

### Server not starting

1. Check if port is in use:

   ```powershell
   netstat -an | findstr :8000
   ```

2. View Task Scheduler logs:
   - Open Task Scheduler (`taskschd.msc`)
   - Navigate to Task Scheduler Library
   - Find "TaskdogServer" and check History tab

### Database errors

1. Ensure data directory exists:

   ```powershell
   mkdir "$env:LOCALAPPDATA\taskdog" -Force
   ```

2. Check file permissions on `tasks.db`

### TUI display issues

Use Windows Terminal for best compatibility. The built-in Command Prompt has limited Unicode support.
