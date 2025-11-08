# Systemd User Service Setup

Taskdog Server can run as a systemd user service for automatic startup and management.

## Installation

The systemd service is automatically installed when you run:

```bash
make install
```

This will:
1. Install the `taskdog-server` command globally
2. Copy the systemd service file to `~/.config/systemd/user/taskdog-server.service`
3. Enable the service for automatic startup
4. Reload the systemd daemon

## Starting the Service

After installation, start the service with:

```bash
systemctl --user start taskdog-server
```

Check the status:

```bash
systemctl --user status taskdog-server
```

## Service Management

### View Logs

```bash
# Follow logs in real-time
journalctl --user -u taskdog-server -f

# View recent logs
journalctl --user -u taskdog-server -n 50

# View logs since boot
journalctl --user -u taskdog-server -b
```

### Stop the Service

```bash
systemctl --user stop taskdog-server
```

### Restart the Service

```bash
systemctl --user restart taskdog-server
```

### Disable Auto-Start

```bash
systemctl --user disable taskdog-server
```

### Re-enable Auto-Start

```bash
systemctl --user enable taskdog-server
```

## Configuration

The default service configuration:
- **Host**: 127.0.0.1 (local only)
- **Port**: 8000
- **Workers**: 4
- **Auto-restart**: Yes (on failure)
- **Data directory**: `~/.local/share/taskdog/`

### Customizing the Service

To customize the service (host, port, workers, etc.), edit the service file:

```bash
# Edit the service file
nano ~/.config/systemd/user/taskdog-server.service

# Reload systemd configuration
systemctl --user daemon-reload

# Restart the service
systemctl --user restart taskdog-server
```

Example modifications:

**Change host and port (listen on all interfaces):**
```ini
ExecStart=%h/.local/bin/taskdog-server --host 0.0.0.0 --port 9000 --workers 4
```

**Enable development mode with auto-reload:**
```ini
ExecStart=%h/.local/bin/taskdog-server --host 127.0.0.1 --port 8000 --reload
```

**Change number of workers:**
```ini
ExecStart=%h/.local/bin/taskdog-server --host 127.0.0.1 --port 8000 --workers 8
```

## Troubleshooting

### Service Won't Start

1. Check logs:
   ```bash
   journalctl --user -u taskdog-server -n 50
   ```

2. Verify the command works manually:
   ```bash
   ~/.local/bin/taskdog-server --help
   ```

3. Check if the port is already in use:
   ```bash
   ss -tlnp | grep 8000
   ```

### Service Crashes on Startup

- Check permissions on the data directory:
  ```bash
  ls -ld ~/.local/share/taskdog/
  ```

- Ensure the database file is not corrupted:
  ```bash
  sqlite3 ~/.local/share/taskdog/tasks.db "PRAGMA integrity_check;"
  ```

### Logs Not Appearing

- Ensure journald is running:
  ```bash
  systemctl --user status
  ```

- Check systemd user service status:
  ```bash
  loginctl user-status
  ```

### Service Not Auto-Starting on Boot

Enable lingering for your user (allows user services to run without login):

```bash
loginctl enable-linger $USER
```

## Uninstallation

To remove the systemd service:

```bash
make uninstall
```

This will:
1. Stop the service
2. Disable auto-start
3. Remove the service file
4. Reload the systemd daemon
5. Uninstall the `taskdog-server` command

## Manual Installation

If you prefer to manage the service manually without `make install`:

```bash
# Copy service file
mkdir -p ~/.config/systemd/user
cp packages/taskdog-server/taskdog-server.service ~/.config/systemd/user/

# Reload systemd
systemctl --user daemon-reload

# Enable and start
systemctl --user enable taskdog-server
systemctl --user start taskdog-server
```

## Security Considerations

The default service configuration includes security hardening:
- `NoNewPrivileges=true`: Prevents privilege escalation
- `PrivateTmp=true`: Uses private /tmp directory
- `ProtectSystem=strict`: Makes most of the filesystem read-only
- `ProtectHome=read-only`: Makes home directory read-only (except data directory)
- `ReadWritePaths=%h/.local/share/taskdog`: Allows writes only to data directory

These settings provide defense-in-depth protection while allowing the service to function normally.

## Using Taskdog CLI with the Server

Once the server is running, you can configure the CLI to use it:

```bash
# Set the API URL environment variable
export TASKDOG_API_URL=http://127.0.0.1:8000

# Now CLI commands will use the API server
taskdog table
taskdog add "New task"
```

To make this permanent, add to your shell configuration (~/.bashrc, ~/.zshrc, etc.):

```bash
echo 'export TASKDOG_API_URL=http://127.0.0.1:8000' >> ~/.bashrc
```
