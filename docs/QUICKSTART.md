# Taskdog Quick Setup Guide

Get started with Taskdog in 5 minutes!

## Prerequisites

- Python 3.11+ (workspace root) or 3.13+ (individual packages)
- [uv](https://github.com/astral-sh/uv) package manager

## Step 1: Install Taskdog (2 minutes)

```bash
# Clone the repository
git clone https://github.com/Kohei-Wada/taskdog.git
cd taskdog

# Install both CLI/TUI and API server
make install
```

This installs two commands:

- `taskdog` - CLI and TUI interface
- `taskdog-server` - API server (required for taskdog to work)

## Step 2: Configure Authentication (2 minutes)

Taskdog uses API key authentication by default. You need to configure both server and client.

### 2a. Generate API Key

```bash
# Generate a secure API key
python -c "import secrets; print(f'sk-{secrets.token_hex(24)}')"
# Example output: sk-a1b2c3d4e5f6...
```

### 2b. Configure Server

```bash
# Create config directory
mkdir -p ~/.config/taskdog

# Create server config with your API key
cat > ~/.config/taskdog/server.toml << 'EOF'
[auth]
enabled = true

[[auth.api_keys]]
name = "my-client"
key = "sk-YOUR-GENERATED-KEY-HERE"  # Replace with your key
EOF

# Secure the file (contains secrets)
chmod 600 ~/.config/taskdog/server.toml
```

### 2c. Configure CLI/TUI

```bash
# Create CLI config with the same API key
cat > ~/.config/taskdog/cli.toml << 'EOF'
[api]
host = "127.0.0.1"
port = 8000
api_key = "sk-YOUR-GENERATED-KEY-HERE"  # Same key as server.toml

[ui]
theme = "textual-dark"
EOF
```

**Important**: The `api_key` in `cli.toml` must match one of the keys in `server.toml`.

## Step 3: Start the Server (1 minute)

### Option A: Docker (Recommended for isolation)

```bash
# Build and run the container
docker build -f contrib/docker/Dockerfile -t taskdog-server .
docker run -d --name taskdog-server -p 8000:8000 -v taskdog-data:/data taskdog-server

# Verify it's running
curl http://localhost:8000/health
```

See [contrib/docker/README.md](../contrib/docker/README.md) for more details.

### Option B: Manual Start (Quick Test)

```bash
# Start the server in a terminal
taskdog-server

# Keep this terminal running
```

### Option C: Systemd Service (Linux, Recommended for local)

```bash
# Start the service
systemctl --user start taskdog-server

# Enable auto-start on boot
systemctl --user enable taskdog-server

# Check status
systemctl --user status taskdog-server
```

The server will now:

- Start automatically when you log in
- Restart automatically if it crashes
- Run in the background

## Step 4: Verify Everything Works (1 minute)

```bash
# In a new terminal, test the CLI
taskdog table

# If you see an empty table (or a list of tasks), you're ready!
```

## Quick Tour

Now that everything is set up, try these commands:

```bash
# Add your first task
taskdog add "Learn Taskdog" --priority 10

# View tasks in a table
taskdog table

# Start working on the task
taskdog start 1

# View in interactive TUI
taskdog tui
```

### TUI Keyboard Shortcuts

Once in the TUI (`taskdog tui`):

- `a` - Add new task
- `s` - Start selected task
- `d` - Complete (done) task
- `i` - Show task details
- `q` - Quit
- `/` - Search
- `S` - Change sort order

## Common Issues & Solutions

### Error: "Cannot connect to API server"

**Problem**: Server is not running

**Solution**:

```bash
# Check if server is running
systemctl --user status taskdog-server

# Or manually check
curl http://127.0.0.1:8000/health

# If not running, start it (see Step 3)
taskdog-server
```

### Error: Connection refused

**Problem**: Port mismatch between config and server

**Solution**:

```bash
# Check what port the server is using
systemctl --user status taskdog-server  # Look for --port in the command

# Make sure config matches
cat ~/.config/taskdog/cli.toml  # Check [api] port value

# Update config if needed
nano ~/.config/taskdog/cli.toml
```

### Server won't start

**Problem**: Port already in use

**Solution**:

```bash
# Check what's using port 8000
ss -tlnp | grep 8000

# Use a different port
taskdog-server --port 8001

# Update config to match
# Edit ~/.config/taskdog/cli.toml: port = 8001
```

### Error: Authentication failed (401)

**Problem**: API key mismatch or missing

**Solution**:

```bash
# Check server config has the key
grep -A2 "api_keys" ~/.config/taskdog/server.toml

# Check CLI config has matching key
grep "api_key" ~/.config/taskdog/cli.toml

# Verify keys match (copy-paste to compare)
```

## MCP Server Setup (Optional)

Use Claude Desktop or other MCP-compatible AI clients to manage tasks via natural language.

### Install MCP Server

```bash
# From taskdog workspace root
make install-mcp

# Or install globally
uv tool install taskdog-mcp
```

### Configure MCP

```bash
# Create MCP config
cat > ~/.config/taskdog/mcp.toml << 'EOF'
[api]
host = "127.0.0.1"
port = 8000
api_key = "sk-YOUR-GENERATED-KEY-HERE"  # Same key as server.toml

[server]
name = "taskdog"
log_level = "INFO"
EOF
```

### Configure Claude Desktop

Add to Claude Desktop config:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "taskdog": {
      "command": "taskdog-mcp"
    }
  }
}
```

Restart Claude Desktop after configuration.

### Test MCP

Ask Claude Desktop:

- "Show me today's tasks"
- "Create a task to review the PR"
- "Start task 42"

See [taskdog-mcp README](../packages/taskdog-mcp/README.md) for more details.

## Next Steps

- Read the [full README](../README.md) for all features
- Check [CLAUDE.md](../CLAUDE.md) for architecture details
- Explore optimization algorithms: `taskdog optimize --help`
- Try the Gantt chart: `taskdog gantt`
- Add dependencies: `taskdog add-dependency TASK_ID DEPENDS_ON_ID`
- Set up MCP for AI-assisted task management

## Environment Variable Alternative

Instead of editing the config file, you can set environment variables:

```bash
# Add to your shell profile (~/.bashrc, ~/.zshrc, etc.)
export TASKDOG_API_HOST=127.0.0.1
export TASKDOG_API_PORT=8000
export TASKDOG_API_KEY=sk-your-api-key

# Or set them temporarily
TASKDOG_API_KEY=sk-your-key taskdog table
```

Note: Environment variables take precedence over config file.

## Uninstall

If you need to remove Taskdog:

```bash
cd /path/to/taskdog

# Stop and remove systemd service (if using)
systemctl --user stop taskdog-server
systemctl --user disable taskdog-server

# Uninstall commands
make uninstall

# Optional: Remove data and config
rm -rf ~/.local/share/taskdog
rm -rf ~/.config/taskdog
```

## Getting Help

- Issues: https://github.com/Kohei-Wada/taskdog/issues
- Documentation: See [README.md](../README.md)
- CLI help: `taskdog --help`
- Command help: `taskdog <command> --help`
