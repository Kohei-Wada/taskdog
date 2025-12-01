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

## Step 2: Configure API Connection (1 minute)

Create the configuration file:

```bash
# Create config directory
mkdir -p ~/.config/taskdog

# Create config file
cat > ~/.config/taskdog/config.toml << 'EOF'
[api]
enabled = true
host = "127.0.0.1"
port = 8000
EOF
```

**Important**: The `[api]` section is required. Without it, the CLI/TUI will not work.

## Step 3: Start the Server (1 minute)

### Option A: Manual Start (Quick Test)

```bash
# Start the server in a terminal
taskdog-server

# Keep this terminal running
```

### Option B: Systemd Service (Recommended)

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

### Error: "API mode is required"

**Problem**: Config file missing or `enabled = false`

**Solution**:

```bash
# Check if config exists
cat ~/.config/taskdog/config.toml

# If missing or wrong, recreate it (see Step 2)
```

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
cat ~/.config/taskdog/config.toml  # Check [api] port value

# Update config if needed
nano ~/.config/taskdog/config.toml
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
# Edit ~/.config/taskdog/config.toml: port = 8001
```

## Next Steps

- Read the [full README](../README.md) for all features
- Check [CLAUDE.md](../CLAUDE.md) for architecture details
- Explore optimization algorithms: `taskdog optimize --help`
- Try the Gantt chart: `taskdog gantt`
- Add dependencies: `taskdog add-dependency TASK_ID DEPENDS_ON_ID`

## Environment Variable Alternative

Instead of editing the config file, you can set an environment variable:

```bash
# Add to your shell profile (~/.bashrc, ~/.zshrc, etc.)
export TASKDOG_API_URL=http://127.0.0.1:8000

# Or set it temporarily
TASKDOG_API_URL=http://127.0.0.1:8000 taskdog table
```

Note: Environment variable takes precedence over config file.

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
