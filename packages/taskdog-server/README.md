# taskdog-server

FastAPI server for Taskdog task management system.

## Overview

This package provides a REST API for all Taskdog functionality including:

- Task CRUD operations
- Task lifecycle management (start, complete, pause, cancel, reopen)
- Task relationships (dependencies, tags)
- Time tracking and logging
- Schedule optimization
- Statistics and analytics
- WebSocket real-time updates

## Installation

```bash
pip install taskdog-server
```

For development:

```bash
pip install -e ".[dev]"
```

## Usage

Start the server:

```bash
taskdog-server
```

With custom options:

```bash
taskdog-server --host 0.0.0.0 --port 3000 --workers 4
```

Development mode with auto-reload:

```bash
taskdog-server --reload
```

## API Documentation

Once the server is running, visit:

- Interactive API docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

For complete API reference, see [docs/API.md](../../docs/API.md).

## Authentication

Configure API key authentication in `~/.config/taskdog/server.toml`:

```toml
[auth]
enabled = true

[[auth.api_keys]]
name = "my-client"
key = "your-secret-key"
```

Clients authenticate via `X-Api-Key` header:

```bash
curl -H "X-Api-Key: your-secret-key" http://localhost:8000/api/v1/tasks/
```

See [Authentication Documentation](../../docs/API.md#authentication) for details.

## WebSocket Real-time Updates

Connect to `/ws` for real-time task notifications:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws?token=your-api-key');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.type);  // task_created, task_updated, etc.
};
```

**Event types:**

- `task_created` - New task created
- `task_updated` - Task fields updated
- `task_deleted` - Task deleted
- `task_status_changed` - Task status changed
- `schedule_optimized` - Schedule optimization completed

**Note:** WebSocket requires `--workers 1` (default). Multiple workers are not supported for WebSocket.

## Configuration

Server configuration: `~/.config/taskdog/server.toml`

```toml
[auth]
enabled = true

[[auth.api_keys]]
name = "my-client"
key = "your-secret-key"

[audit]
enabled = false
```

Core configuration: `~/.config/taskdog/core.toml`

```toml
[region]
country = "JP"
```

See [Configuration Guide](../../docs/CONFIGURATION.md) for all options.

## Architecture

The server uses:

- **FastAPI**: Modern, fast web framework
- **Pydantic**: Data validation with type hints
- **uvicorn**: ASGI server
- **taskdog-core**: Core business logic and infrastructure

### API Routers

- `tasks.py` - Task CRUD operations
- `lifecycle.py` - Task status changes
- `relationships.py` - Dependencies and tags
- `analytics.py` - Statistics and reporting
- `notes.py` - Markdown notes
- `websocket.py` - Real-time updates

### Dependency Injection

Controllers are injected via FastAPI dependencies:

```python
CrudControllerDep = Annotated[TaskCrudController, Depends(get_crud_controller)]
```

## Related Packages

- [taskdog-core](../taskdog-core/): Core business logic used by this package
- [taskdog-ui](../taskdog-ui/): CLI and TUI interfaces connecting to this server
- [taskdog-client](../taskdog-client/): HTTP client library for API access
- [taskdog-mcp](../taskdog-mcp/): MCP server for Claude Desktop integration

## Testing

```bash
pytest tests/
```

## Deployment

### Systemd (Linux)

```bash
systemctl --user start taskdog-server
systemctl --user enable taskdog-server
```

### Docker

```bash
docker pull ghcr.io/kohei-wada/taskdog-server:main
docker run -d -p 8000:8000 -v taskdog-data:/data ghcr.io/kohei-wada/taskdog-server:main
```

See [contrib/README.md](../../contrib/README.md) for deployment details.

## License

MIT
