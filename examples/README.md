# Configuration Examples

This directory contains example configuration files for Taskdog.

## Configuration Files

Taskdog uses **separate configuration files** for clear separation of concerns:

### 1. `core.toml` - Core Configuration

**Purpose**: Business logic settings

**Used by**: `taskdog-server` (API server)

**Location**: `~/.config/taskdog/core.toml`

**Contains**:

- Task defaults (default priority)
- Optimization settings (max hours per day, default algorithm)
- Time settings (default start/end hours)
- Region settings (holiday calendar)
- Storage settings (database location)
- API settings (CORS)

**When to use**: Configure business logic behavior

### 2. `cli.toml` - CLI Configuration

**Purpose**: CLI/TUI infrastructure settings

**Used by**: `taskdog` (CLI) and `taskdog tui` (TUI)

**Location**: `~/.config/taskdog/cli.toml`

**Contains**:

- API connection settings (host, port)
- Future: Keybindings customization
- Future: Theme/color preferences

**When to use**: Configure how CLI/TUI connects to the server

### 3. `mcp.toml` - MCP Server Configuration

**Purpose**: MCP server settings for Claude Desktop integration

**Used by**: `taskdog-mcp` (MCP server)

**Location**: `~/.config/taskdog/mcp.toml`

**Contains**:

- API connection settings (host, port, api_key)
- MCP server settings (name, log_level)

**When to use**: Configure the MCP server for Claude Desktop

**Important**: The `api_key` setting is required. It must match a key configured in `server.toml`.

## Quick Start

### Default Setup (Recommended)

If you don't create any config files, Taskdog uses sensible defaults:

```bash
# Start server with defaults
taskdog-server  # Listens on 127.0.0.1:8000

# Use CLI with defaults
taskdog table   # Connects to 127.0.0.1:8000
```

No configuration needed!

### Custom Setup

1. **Copy example files**:

   ```bash
   mkdir -p ~/.config/taskdog
   cp examples/core.toml ~/.config/taskdog/
   cp examples/cli.toml ~/.config/taskdog/
   cp examples/mcp.toml ~/.config/taskdog/  # For MCP/Claude Desktop
   ```

2. **Edit as needed**:

   ```bash
   # Core config (business logic)
   $EDITOR ~/.config/taskdog/core.toml

   # CLI config (API connection)
   $EDITOR ~/.config/taskdog/cli.toml
   ```

3. **Restart server** (if core.toml changed):

   ```bash
   systemctl --user restart taskdog-server
   ```

## Configuration File Relationship

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                                   User                                      │
└────────┬────────────────────────────┬────────────────────────┬──────────────┘
         │                            │                        │
         │ Uses                       │ Uses                   │ Uses
         ▼                            ▼                        ▼
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   taskdog (CLI)     │    │  taskdog-server     │    │   taskdog-mcp       │
│   taskdog tui (TUI) │───►│  (API Server)       │◄───│   (MCP Server)      │
└─────────────────────┘HTTP└─────────────────────┘HTTP└─────────────────────┘
         │                       │         │                   │
         │ Reads                 │ Reads   │ Reads             │ Reads
         ▼                       ▼         ▼                   ▼
┌─────────────────┐    ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐
│   cli.toml      │    │ core.toml   │ │ server.toml │ │   mcp.toml      │
│ (CLI Settings)  │    │ (Business)  │ │ (Server)    │ │ (MCP Settings)  │
└─────────────────┘    └─────────────┘ └─────────────┘ └─────────────────┘
• API host/port         • Task defaults  • Auth/API keys  • API host/port
• UI theme              • Optimization   • Audit logging  • Server name
• Future: keybindings   • Holidays       • WebSocket      • Log level
                        • Database
```

## Why Two Config Files?

This separation provides several benefits:

1. **Clear Responsibilities**:
   - Server owns business logic (what priorities? what holidays?)
   - CLI owns infrastructure (which server to connect to?)

2. **Simpler Configuration**:
   - CLI users only need API connection settings
   - Server admins control all business logic centrally

3. **Flexible Deployment**:
   - CLI can connect to remote servers easily
   - Multiple CLIs can use the same server config

4. **Future Extensibility**:
   - CLI config can add UI-specific settings (keybindings, themes)
   - Server config can add more business logic settings
   - No mixing of concerns

## Common Scenarios

### Scenario 1: Default Local Setup

**No config files needed!**

```bash
taskdog-server  # Uses defaults
taskdog table   # Uses defaults
```

### Scenario 2: Custom Server Port

**Core** (`~/.config/taskdog/core.toml`):

```toml
[api]
enabled = true
port = 3000
```

**CLI** (`~/.config/taskdog/cli.toml`):

```toml
[api]
port = 3000
```

### Scenario 3: Remote Server

**Server** (on remote machine):

```toml
[api]
enabled = true
host = "0.0.0.0"  # Listen on all interfaces
port = 8000
```

**CLI** (on local machine):

```toml
[api]
host = "192.168.1.100"  # Remote server IP
port = 8000
```

### Scenario 4: Custom Business Logic

**Only edit core.toml**:

```toml
[task]
default_priority = 7  # Higher default priority

[optimization]
max_hours_per_day = 8.0  # Longer work days
default_algorithm = "balanced"

[region]
country = "US"  # Use US holidays
```

CLI needs no changes - it automatically uses server's settings.

## Environment Variables

Both configs support environment variable overrides:

### CLI (`cli.toml`)

```bash
export TASKDOG_API_HOST=192.168.1.100
export TASKDOG_API_PORT=3000
taskdog table
```

### Core (`core.toml`)

No environment variables currently supported. Use config file or command-line args:

```bash
taskdog-server --host 0.0.0.0 --port 3000
```

## Migration from Old Single-Config Setup

If you're upgrading from an older version:

1. **Keep your `core.toml`** - Server will continue using it
2. **Optionally create `cli.toml`** - Only if you need non-default API settings
3. **No data migration needed** - Database format unchanged

The old single-config approach still works for the server. CLI just gained its own separate config.

## Troubleshooting

### "Cannot connect to API server"

**Problem**: CLI can't reach server

**Check**:

1. Is server running? `systemctl --user status taskdog-server`
2. Check CLI config: `cat ~/.config/taskdog/cli.toml`
3. Check core config: `cat ~/.config/taskdog/core.toml`
4. Test connection: `curl http://127.0.0.1:8000/health`

**Common fixes**:

- Start server: `systemctl --user start taskdog-server`
- Match ports in both configs
- Use `127.0.0.1` (not `0.0.0.0`) in CLI config

### "Invalid configuration"

**Problem**: Config file has syntax errors

**Fix**:

1. Validate TOML syntax: Copy example file and edit carefully
2. Check for typos in section names: `[api]`, `[task]`, etc.
3. Ensure correct types: numbers without quotes, strings with quotes

### Server doesn't use my defaults

**Problem**: Custom priority/algorithm not applied

**Check**:

1. Are you editing the right file? Server uses `core.toml`, not `cli.toml`
2. Did you restart server? `systemctl --user restart taskdog-server`
3. Check file location: `~/.config/taskdog/core.toml`

## See Also

- [CLI Configuration Documentation](../packages/taskdog-ui/CLI_CONFIG.md)
- [Main README](../README.md)
- [Architecture Documentation](../CLAUDE.md)
