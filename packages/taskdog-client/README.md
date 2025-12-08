# taskdog-client

HTTP API client library for Taskdog server.

## Overview

This package provides a type-safe HTTP client for communicating with the Taskdog API server. It handles authentication, error mapping, and response conversion to domain DTOs.

**Use cases:**

- Building custom CLI tools
- Integrating Taskdog with other systems
- Creating automated workflows
- Testing API endpoints

## Installation

```bash
pip install taskdog-client
```

For development:

```bash
pip install -e ".[dev]"
```

## Client Classes

| Client | Purpose |
|--------|---------|
| `TaskClient` | Task CRUD operations (create, update, delete, archive) |
| `LifecycleClient` | Status changes (start, complete, pause, cancel, reopen) |
| `RelationshipClient` | Dependencies and tags |
| `QueryClient` | List tasks, get task details |
| `AnalyticsClient` | Statistics and Gantt data |
| `NotesClient` | Task notes (markdown) |
| `AuditClient` | Audit log access |
| `BaseApiClient` | Base class with common HTTP logic |

## Usage Example

```python
from taskdog_client import TaskClient, LifecycleClient, QueryClient

# Create clients
base_url = "http://127.0.0.1:8000"
api_key = "your-api-key"  # Optional, for authenticated servers

task_client = TaskClient(base_url, api_key)
lifecycle_client = LifecycleClient(base_url, api_key)
query_client = QueryClient(base_url, api_key)

# Create a task
task = task_client.create_task(
    name="My Task",
    priority=100,
    estimated_duration=8.0,
    tags=["backend"]
)
print(f"Created task: {task.id}")

# List tasks
tasks = query_client.list_tasks(status="pending")
for t in tasks:
    print(f"- {t.name} (ID: {t.id})")

# Start a task
lifecycle_client.start_task(task.id)

# Complete a task
lifecycle_client.complete_task(task.id)
```

## Error Handling

Clients raise exceptions from `taskdog_core.domain.exceptions`:

```python
from taskdog_core.domain.exceptions import TaskNotFoundException, TaskValidationError

try:
    task_client.get_task(999)
except TaskNotFoundException:
    print("Task not found")
except TaskValidationError as e:
    print(f"Validation error: {e}")
```

## Configuration

Clients accept optional configuration:

```python
from taskdog_client import TaskClient

# Basic usage (no auth)
client = TaskClient("http://127.0.0.1:8000")

# With API key authentication
client = TaskClient(
    base_url="http://127.0.0.1:8000",
    api_key="your-secret-key"
)

# Custom timeout (in seconds)
client = TaskClient(
    base_url="http://127.0.0.1:8000",
    timeout=30.0
)
```

## Dependencies

- `taskdog-core`: Domain DTOs and exceptions
- `httpx`: HTTP client library

## Related Packages

- [taskdog-core](../taskdog-core/): Domain DTOs used by this package
- [taskdog-server](../taskdog-server/): API server this client connects to
- [taskdog-ui](../taskdog-ui/): CLI/TUI that uses this client
- [taskdog-mcp](../taskdog-mcp/): MCP server that uses this client

## Testing

```bash
pytest tests/
```

## License

MIT
