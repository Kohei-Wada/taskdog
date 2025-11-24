# CLI Configuration

This document describes the configuration system for Taskdog CLI/TUI.

## Overview

Taskdog CLI/TUI uses a separate configuration file (`cli.toml`) from the server's `config.toml`. This separation clarifies that:

- **CLI config** (`cli.toml`): Infrastructure settings for the UI layer (API connection, keybindings)
- **Server config** (`config.toml`): Business logic settings (defaults, optimization, holidays)

The CLI/TUI is a thin client that delegates all business logic to the server. All task defaults (priority, max_hours_per_day, etc.) are handled by the server's controllers, not by the CLI.

## Configuration File Location

The CLI configuration file is located at:

```
~/.config/taskdog/cli.toml
```

Or, if `XDG_CONFIG_HOME` is set:

```
$XDG_CONFIG_HOME/taskdog/cli.toml
```

**Example**: See `../../examples/cli.toml` for a fully documented example configuration.

## Configuration Structure

### [api] Section

API connection settings for connecting to the taskdog-server.

```toml
[api]
host = "127.0.0.1"  # API server hostname (default: "127.0.0.1")
port = 8000          # API server port (default: 8000)
```

**Note**: CLI/TUI always requires the API server to be running. There is no standalone mode.

### [keybindings] Section (Future Feature)

Custom keybindings for the TUI. Not yet implemented.

```toml
[keybindings]
# Future: Custom keybindings for TUI
# quit = "q"
# add = "a"
# start = "s"
```

## Environment Variables

Environment variables have the highest priority and override settings from `cli.toml`.

| Variable | Description | Default |
|----------|-------------|---------|
| `TASKDOG_API_HOST` | API server hostname | `127.0.0.1` |
| `TASKDOG_API_PORT` | API server port | `8000` |

### Examples

```bash
# Connect to remote server
export TASKDOG_API_HOST=192.168.1.100
export TASKDOG_API_PORT=3000
taskdog table

# Or inline
TASKDOG_API_HOST=192.168.1.100 taskdog table
```

## Priority Order

Configuration values are loaded with the following priority (highest to lowest):

1. **Environment variables** (`TASKDOG_API_HOST`, `TASKDOG_API_PORT`)
2. **cli.toml file** (`~/.config/taskdog/cli.toml`)
3. **Defaults** (host: `127.0.0.1`, port: `8000`)

## Minimal Example

If you don't create a `cli.toml` file, Taskdog will use defaults:

- API server: `http://127.0.0.1:8000`

This works out-of-the-box if you start the server with default settings:

```bash
taskdog-server  # Starts on 127.0.0.1:8000
taskdog table   # CLI connects to 127.0.0.1:8000
```

## Custom Server Configuration

If you run the server on a custom host/port:

```bash
taskdog-server --host 0.0.0.0 --port 3000
```

Create `~/.config/taskdog/cli.toml`:

```toml
[api]
host = "127.0.0.1"
port = 3000
```

Or use environment variables:

```bash
export TASKDOG_API_PORT=3000
taskdog table
```

## Remote Server Connection

To connect CLI/TUI to a remote server:

```toml
[api]
host = "192.168.1.100"
port = 8000
```

**Security Note**: The API server does not have authentication. Only use this for trusted networks or localhost.

## Business Logic Configuration

Business logic settings (task defaults, optimization parameters, holidays) are configured in the **server's** `config.toml`, not in the CLI's `cli.toml`.

Examples of server-side settings:

- Default task priority
- Max hours per day for optimization
- Default optimization algorithm
- Holiday calendar
- Default work hours (9 AM - 6 PM)

These are configured in `~/.config/taskdog/config.toml` and loaded by the server. See the main README or `packages/taskdog-server/README.md` for server configuration details.

## Migration from Old Config

If you're upgrading from an older version that used a single `config.toml` file:

1. **Keep your `config.toml`** - It's now only used by the server
2. **Optionally create `cli.toml`** - Only needed if you use non-default API settings
3. **No migration needed** - CLI will use defaults (127.0.0.1:8000) if `cli.toml` doesn't exist

The separation means:

- `config.toml`: Server reads this (business logic settings)
- `cli.toml`: CLI/TUI reads this (infrastructure settings)
- No shared configuration file

## Troubleshooting

### "Cannot connect to API server"

**Problem**: CLI shows connection error

**Solutions**:

1. Check if server is running:
   ```bash
   systemctl --user status taskdog-server
   # Or manually:
   taskdog-server
   ```

2. Check server host/port:
   ```bash
   # Server default: 127.0.0.1:8000
   # CLI default: 127.0.0.1:8000
   ```

3. Verify CLI config matches server config:
   ```bash
   cat ~/.config/taskdog/cli.toml
   ```

4. Test connection manually:
   ```bash
   curl http://127.0.0.1:8000/health
   # Should return: {"status":"healthy"}
   ```

### "Invalid configuration"

**Problem**: Config file has syntax errors

**Solution**:

1. Check TOML syntax:
   ```bash
   cat ~/.config/taskdog/cli.toml
   ```

2. Common mistakes:
   - Missing quotes around strings
   - Wrong section names (`[api]` not `[API]`)
   - Invalid port (must be integer)

3. Start fresh with minimal config:
   ```toml
   [api]
   host = "127.0.0.1"
   port = 8000
   ```

## See Also

- Main documentation: `README.md`
- Server configuration: `packages/taskdog-server/README.md`
- Architecture: `CLAUDE.md`
