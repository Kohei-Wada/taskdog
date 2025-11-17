# Configuration Examples

This directory contains example configuration files for taskdog.

## Files

- **server.toml.example** - Server configuration for taskdog-server
- **client.toml.example** - Client configuration for taskdog CLI/TUI

## Usage

### Server Configuration

Copy the example to your config directory:

```bash
# Using XDG directories (recommended)
cp examples/config/server.toml.example ~/.config/taskdog/server.toml

# Or use environment variable
cp examples/config/server.toml.example $XDG_CONFIG_HOME/taskdog/server.toml
```

Then edit `~/.config/taskdog/server.toml` to customize:
- Time settings (default work hours)
- Regional settings (country for holiday detection)
- Storage settings (database location)
- Task defaults (default priority)

### Client Configuration

Copy the example to your config directory:

```bash
# Using XDG directories (recommended)
cp examples/config/client.toml.example ~/.config/taskdog/client.toml

# Or use environment variable
cp examples/config/client.toml.example $XDG_CONFIG_HOME/taskdog/client.toml
```

Then edit `~/.config/taskdog/client.toml` to customize:
- Optimization defaults (max hours, algorithm)
- API connection (server URL, host, port)

## Configuration Priority

Settings are loaded in the following order (later overrides earlier):

1. Default values (hardcoded)
2. Configuration file (`server.toml` or `client.toml`)
3. Environment variables (e.g., `TASKDOG_API_URL`)
4. Command-line arguments

## Notes

- Configuration files are optional - taskdog will use sensible defaults if not present
- Server and client configurations are separate for better modularity
- See `CLAUDE.md` in the repository root for detailed configuration documentation
