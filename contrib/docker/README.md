# Docker Setup

Run Taskdog Server in a Docker container.

## Quick Start

### Using Pre-built Image (Recommended)

```bash
# Pull the latest image from GitHub Container Registry
docker pull ghcr.io/kohei-wada/taskdog-server:main

# Run with data persistence
docker run -d \
  --name taskdog-server \
  -p 8000:8000 \
  -v taskdog-data:/data \
  ghcr.io/kohei-wada/taskdog-server:main

# Verify it's running
curl http://localhost:8000/health
```

### Building from Source

```bash
# Build the image (from repository root)
docker build -f contrib/docker/Dockerfile -t taskdog-server .

# Run with data persistence
docker run -d \
  --name taskdog-server \
  -p 8000:8000 \
  -v taskdog-data:/data \
  taskdog-server

# Verify it's running
curl http://localhost:8000/health
```

## Usage

### Build

```bash
cd /path/to/taskdog
docker build -f contrib/docker/Dockerfile -t taskdog-server .
```

### Run

**Basic (ephemeral data):**

```bash
docker run -d -p 8000:8000 taskdog-server
```

**With data persistence (recommended):**

```bash
docker run -d \
  --name taskdog-server \
  -p 8000:8000 \
  -v taskdog-data:/data \
  taskdog-server
```

**With host directory mount:**

```bash
docker run -d \
  --name taskdog-server \
  -p 8000:8000 \
  -v /path/to/your/data:/data \
  taskdog-server
```

### Stop and Remove

```bash
docker stop taskdog-server
docker rm taskdog-server
```

## Configuration

### Environment Variables

All Taskdog configuration can be set via environment variables with the `TASKDOG_` prefix:

```bash
docker run -d \
  -p 8000:8000 \
  -v taskdog-data:/data \
  -e TASKDOG_OPTIMIZATION_MAX_HOURS_PER_DAY=8 \
  -e TASKDOG_OPTIMIZATION_DEFAULT_ALGORITHM=balanced \
  -e TASKDOG_REGION_COUNTRY=JP \
  taskdog-server
```

**Note:** The database URL uses SQLAlchemy format: `sqlite:////data/tasks.db` (four slashes for absolute path).

See [CONFIGURATION.md](../../docs/CONFIGURATION.md) for all available options.

### Custom Port

```bash
# Map to a different host port
docker run -d -p 3000:8000 -v taskdog-data:/data taskdog-server
```

## Data Persistence

The container stores data in `/data`:

- `tasks.db` - SQLite database with all tasks
- `notes/` - Markdown notes for tasks (if used)

**Important:** Always use a volume mount (`-v`) to persist data across container restarts.

### Backup

```bash
# Stop the container first
docker stop taskdog-server

# Copy data from volume
docker run --rm -v taskdog-data:/data -v $(pwd):/backup alpine \
  tar czf /backup/taskdog-backup.tar.gz -C /data .

# Restart the container
docker start taskdog-server
```

### Restore

```bash
docker run --rm -v taskdog-data:/data -v $(pwd):/backup alpine \
  sh -c "cd /data && tar xzf /backup/taskdog-backup.tar.gz"
```

## Connecting CLI/TUI

The CLI and TUI are installed on your host machine and connect to the containerized server:

```bash
# Install CLI/TUI on host (not in container)
cd /path/to/taskdog
make install-ui

# Configure to connect to Docker container
export TASKDOG_API_URL=http://localhost:8000

# Or create config file
mkdir -p ~/.config/taskdog
cat > ~/.config/taskdog/config.toml << 'EOF'
[api]
host = "127.0.0.1"
port = 8000
EOF

# Use CLI
taskdog table
taskdog add "My first task"

# Use TUI
taskdog tui
```

## Health Check

The container includes a health check that polls `/health` every 30 seconds using Python's `urllib` (no curl needed):

```bash
# Check container health status
docker inspect --format='{{.State.Health.Status}}' taskdog-server

# View health check logs
docker inspect --format='{{json .State.Health}}' taskdog-server | jq

# Manual health check from host
curl http://localhost:8000/health
```

## Logs

```bash
# View logs
docker logs taskdog-server

# Follow logs
docker logs -f taskdog-server
```

## Limitations

- **WebSocket:** The container runs with `--workers 1` (required for WebSocket real-time sync)
- **CLI/TUI:** Must be installed on host, not containerized (interactive terminal required)

## Advanced: taskdog-stack

For more advanced setups including:

- Docker Compose orchestration
- Webhook integration (n8n, etc.)
- External service connections

See [taskdog-stack](https://github.com/Kohei-Wada/taskdog-stack) (coming soon).
