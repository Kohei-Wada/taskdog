# Configuration Guide

Complete guide to configuring Taskdog.

## Table of Contents

- [Configuration File Location](#configuration-file-location)
- [Configuration Priority](#configuration-priority)
- [Configuration Sections](#configuration-sections)
  - [API Settings](#api-settings-required)
  - [UI Settings](#ui-settings)
  - [Optimization Settings](#optimization-settings)
  - [Task Settings](#task-settings)
  - [Time Settings](#time-settings)
  - [Region Settings](#region-settings)
  - [Storage Settings](#storage-settings)
- [Data Storage](#data-storage)
- [Environment Variables](#environment-variables)
- [Examples](#examples)

## Configuration File Location

Taskdog looks for configuration in the following locations (in order):

1. `$XDG_CONFIG_HOME/taskdog/config.toml`
2. `~/.config/taskdog/config.toml` (fallback)

Create the directory if it doesn't exist:

```bash
mkdir -p ~/.config/taskdog
```

## Configuration Priority

Settings are resolved in the following order (highest to lowest priority):

1. **Environment variables** (e.g., `TASKDOG_API_URL`)
2. **CLI arguments** (e.g., `--max-hours-per-day`)
3. **Configuration file** (`config.toml`)
4. **Default values** (hardcoded in application)

## Configuration Sections

### API Settings

The `[api]` section configures API server behavior. Note that connection settings (host/port) are configured separately:

- **Server startup**: Use CLI arguments (`taskdog-server --host 0.0.0.0 --port 3000`)
- **CLI/TUI connection**: Use `cli.toml` or environment variables (see [CLI Configuration](../packages/taskdog-ui/CLI_CONFIG.md))

```toml
[api]
cors_origins = ["http://localhost:3000", "http://localhost:8000"]
```

**Fields:**
- `cors_origins` (list of strings) - Allowed CORS origins for web browser access. Used for future Web UI support.

**Environment variable:** `TASKDOG_API_CORS_ORIGINS` (comma-separated list)

### UI Settings

The `[ui]` section configures TUI appearance.

```toml
[ui]
theme = "textual-dark"        # TUI theme (default: "textual-dark")
```

**Fields:**
- `theme` (string) - TUI color theme. Available options:
  - `textual-dark` - Default dark theme
  - `textual-light` - Light theme
  - `tokyo-night` - Tokyo Night color scheme
  - `dracula` - Dracula color scheme
  - `catppuccin-mocha` - Catppuccin Mocha color scheme

### Optimization Settings

The `[optimization]` section configures schedule optimization behavior.

```toml
[optimization]
max_hours_per_day = 6.0        # Default work hours per day (default: 6.0)
default_algorithm = "greedy"   # Default scheduling algorithm (default: "greedy")
```

**Fields:**
- `max_hours_per_day` (float) - Maximum hours to schedule per day. Used by optimizer to distribute workload.
- `default_algorithm` (string) - Default optimization algorithm. Available options:
  - `greedy` - Schedule highest priority tasks first
  - `balanced` - Distribute workload evenly across days
  - `backward` - Schedule from deadline backwards
  - `priority_first` - Strict priority ordering
  - `earliest_deadline` - Schedule tasks with earliest deadlines first
  - `round_robin` - Rotate through tasks to minimize context switching
  - `dependency_aware` - Prioritize tasks that unblock others
  - `genetic` - Use genetic algorithm for optimization
  - `monte_carlo` - Use Monte Carlo simulation

**CLI Override:**
```bash
taskdog optimize --max-hours-per-day 8 -a balanced
```

### Task Settings

The `[task]` section configures default task properties.

```toml
[task]
default_priority = 5           # Default task priority (default: 5)
```

**Fields:**
- `default_priority` (integer) - Default priority for new tasks. Higher values = higher priority.

**CLI Override:**
```bash
taskdog add "Task name" -p 150
```

### Time Settings

The `[time]` section configures business hours.

```toml
[time]
default_start_hour = 9         # Business day start hour (default: 9)
default_end_hour = 18          # Business day end hour (default: 18)
```

**Fields:**
- `default_start_hour` (integer) - Business day start hour (0-23). Used when scheduling tasks without specific times.
- `default_end_hour` (integer) - Business day end hour (0-23). Used for workload calculations.

**Example:** With `default_start_hour = 9`, scheduling a task for "2025-10-22" will use "2025-10-22 09:00:00".

### Region Settings

The `[region]` section configures regional settings for holiday checking.

```toml
[region]
country = "JP"                 # ISO 3166-1 alpha-2 country code
```

**Fields:**
- `country` (string, optional) - ISO 3166-1 alpha-2 country code for holiday checking.
  - Examples: `"JP"` (Japan), `"US"` (United States), `"GB"` (United Kingdom), `"DE"` (Germany)
  - Default: `None` (no holiday checking)

**Behavior:**
- When set, the optimizer will avoid scheduling tasks on national holidays for the specified country.
- Requires internet connection to fetch holiday data on first use (cached locally).

### Storage Settings

The `[storage]` section configures data persistence.

```toml
[storage]
database_url = "~/.local/share/taskdog/tasks.db"  # SQLite database location
backend = "sqlite"             # Storage backend (default: "sqlite")
```

**Fields:**
- `database_url` (string) - Path to SQLite database file. Supports `~` expansion.
- `backend` (string) - Storage backend type. Currently only `"sqlite"` is supported.

**Default location:** `$XDG_DATA_HOME/taskdog/tasks.db` (fallback: `~/.local/share/taskdog/tasks.db`)

## Data Storage

### Database

**Location:** `$XDG_DATA_HOME/taskdog/tasks.db` (fallback: `~/.local/share/taskdog/tasks.db`)

**Features:**
- Transactional writes with ACID guarantees
- Automatic rollback on errors
- Indexed queries for efficient filtering
- Connection pooling and proper resource management

**Backup:**
```bash
cp ~/.local/share/taskdog/tasks.db ~/.local/share/taskdog/tasks.db.backup
```

### Notes

Task notes are stored as separate markdown files:

**Location:** `$XDG_DATA_HOME/taskdog/notes/` (fallback: `~/.local/share/taskdog/notes/`)

**Format:** One `.md` file per task, named by task ID: `1.md`, `2.md`, etc.

## Environment Variables

Environment variables take precedence over config file settings. This is useful for Docker/Kubernetes deployments where configuration is managed externally.

### Server Configuration Variables

These variables override server configuration (config.toml):

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `TASKDOG_OPTIMIZATION_MAX_HOURS_PER_DAY` | float | `6.0` | Maximum work hours per day |
| `TASKDOG_OPTIMIZATION_DEFAULT_ALGORITHM` | string | `"greedy"` | Default scheduling algorithm |
| `TASKDOG_TASK_DEFAULT_PRIORITY` | int | `5` | Default priority for new tasks |
| `TASKDOG_TIME_DEFAULT_START_HOUR` | int | `9` | Business day start hour |
| `TASKDOG_TIME_DEFAULT_END_HOUR` | int | `18` | Business day end hour |
| `TASKDOG_REGION_COUNTRY` | string | `None` | ISO 3166-1 alpha-2 country code |
| `TASKDOG_STORAGE_BACKEND` | string | `"sqlite"` | Storage backend type |
| `TASKDOG_STORAGE_DATABASE_URL` | string | XDG path | Database file location |
| `TASKDOG_API_CORS_ORIGINS` | string | localhost | Comma-separated CORS origins |

**Example:**

```bash
# Production settings
export TASKDOG_OPTIMIZATION_MAX_HOURS_PER_DAY=8.0
export TASKDOG_TASK_DEFAULT_PRIORITY=3
export TASKDOG_REGION_COUNTRY=US
export TASKDOG_API_CORS_ORIGINS="http://localhost:3000,http://app.example.com"
```

**Note:** Invalid values are logged as warnings and fall back to defaults.

### CLI/TUI Connection Variables

These variables configure how CLI/TUI connect to the API server:

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `TASKDOG_API_HOST` | string | `"127.0.0.1"` | API server host |
| `TASKDOG_API_PORT` | int | `8000` | API server port |

**Example:**

```bash
export TASKDOG_API_HOST=192.168.1.100
export TASKDOG_API_PORT=8000
```

### XDG_CONFIG_HOME

Override config file location:

```bash
export XDG_CONFIG_HOME=/custom/path
# Config file will be: /custom/path/taskdog/config.toml
```

### XDG_DATA_HOME

Override data storage location:

```bash
export XDG_DATA_HOME=/custom/path
# Database will be: /custom/path/taskdog/tasks.db
# Notes will be: /custom/path/taskdog/notes/
```

### EDITOR

Set default text editor for `taskdog note` command:

```bash
export EDITOR=vim
# or
export EDITOR=nano
# or
export EDITOR="code --wait"  # VS Code
```

## Examples

### Minimal Configuration

Bare minimum to get started (most settings have sensible defaults):

```toml
# No configuration needed for basic usage!
# Server: taskdog-server (uses default 127.0.0.1:8000)
# CLI/TUI: Connects to default server automatically
```

### Full Configuration

Complete configuration with all options:

```toml
# API Server Settings (optional)
[api]
cors_origins = ["http://localhost:3000", "http://localhost:8000"]

# UI Settings
[ui]
theme = "tokyo-night"

# Optimization Settings
[optimization]
max_hours_per_day = 8.0
default_algorithm = "balanced"

# Task Settings
[task]
default_priority = 10

# Time Settings
[time]
default_start_hour = 9
default_end_hour = 18

# Region Settings
[region]
country = "JP"

# Storage Settings
[storage]
database_url = "~/.local/share/taskdog/tasks.db"
backend = "sqlite"
```

### Remote API Server

Connect CLI/TUI to API server on different host. Configure in `cli.toml`:

```toml
# ~/.config/taskdog/cli.toml
[api]
host = "192.168.1.100"
port = 8000
```

Or use environment variables:

```bash
export TASKDOG_API_HOST=192.168.1.100
export TASKDOG_API_PORT=8000
```

### Work Schedule Configuration

Configure for 8-hour work days with strict 9-18 schedule:

```toml
[optimization]
max_hours_per_day = 8.0
default_algorithm = "balanced"

[time]
default_start_hour = 9
default_end_hour = 18

[region]
country = "US"  # Avoid US holidays
```

### Custom Theme

Use a specific theme for TUI (configure in `cli.toml`):

```toml
# ~/.config/taskdog/cli.toml
[ui]
theme = "dracula"
```

### Custom Database Location

Store database in custom location:

```toml
[storage]
database_url = "~/Documents/taskdog/my-tasks.db"
backend = "sqlite"
```

## Troubleshooting

### CLI/TUI Commands Not Working

**Error:** "API connection error" or "Cannot connect to server"

**Solution:**
1. Start the API server: `taskdog-server`
2. Verify server is running: `curl http://localhost:8000/health`
3. Check host and port in `cli.toml` match the running server
4. If using non-default port: `taskdog-server --port 3000` and update `cli.toml`

### Theme Not Applied

**Error:** TUI still uses default theme

**Solution:**
1. Ensure `[ui]` section is present in `~/.config/taskdog/config.toml`
2. Restart TUI: `taskdog tui`
3. Check theme name spelling (must match exactly)

### Optimizer Not Respecting Hours Limit

**Error:** Tasks scheduled for more hours than max_hours_per_day

**Solution:**
1. Fixed tasks (`is_fixed = true`) count towards daily limit but cannot be moved
2. Check if multiple tasks overlap in schedule
3. Increase `max_hours_per_day` if needed
4. Use `--force` flag to re-optimize: `taskdog optimize --force`

### Database Not Found

**Error:** "Database file not found" or "No such file or directory"

**Solution:**
1. Database is created automatically on first use
2. Ensure parent directory exists: `mkdir -p ~/.local/share/taskdog`
3. Check `database_url` path in config file
4. Verify permissions: `ls -la ~/.local/share/taskdog/`

## Best Practices

1. **Commit config to version control** - Track configuration changes (remove sensitive data if any)
2. **Use environment variables for secrets** - If adding authentication in future
3. **Backup database regularly** - `cp` database file before major changes
4. **Start with defaults** - Only configure what you need to change
5. **Document custom settings** - Add comments explaining why you changed defaults
6. **Test configuration changes** - Run `taskdog table` after config changes to verify
7. **Use consistent time settings** - Match `default_start_hour` with your actual work schedule
8. **Set region for accurate holidays** - Helps optimizer avoid scheduling on holidays

## See Also

- [CLI Commands Reference](COMMANDS.md) - Complete command reference
- [API Reference](API.md) - REST API documentation
- [README](../README.md) - Main documentation
