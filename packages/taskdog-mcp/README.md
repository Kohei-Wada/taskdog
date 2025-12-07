# taskdog-mcp

MCP (Model Context Protocol) server for Taskdog, enabling Claude Desktop and other MCP-compatible AI clients to interact with your task management system.

## Features

- **Task Management**: Create, read, update, delete tasks via natural language
- **Task Lifecycle**: Start, complete, pause, cancel, reopen tasks
- **Task Decomposition**: AI-assisted breakdown of large tasks into subtasks
- **Queries**: Get today's tasks, statistics, executable tasks

## Installation

```bash
# From the taskdog workspace root
make install-mcp

# Or install globally
uv tool install taskdog-mcp
```

## Configuration

Create `~/.config/taskdog/mcp.toml`:

```toml
[api]
host = "127.0.0.1"
port = 8000
api_key = ""  # Optional, for authenticated servers

[server]
name = "taskdog"
log_level = "INFO"
```

Environment variables override config file:

- `TASKDOG_API_HOST`
- `TASKDOG_API_PORT`
- `TASKDOG_API_KEY`
- `TASKDOG_MCP_NAME`
- `TASKDOG_MCP_LOG_LEVEL`

## Claude Desktop Setup

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "taskdog": {
      "command": "taskdog-mcp"
    }
  }
}
```

Or with uv (for development):

```json
{
  "mcpServers": {
    "taskdog": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/taskdog/packages/taskdog-mcp",
        "run",
        "taskdog-mcp"
      ]
    }
  }
}
```

## Available Tools

### Task CRUD

- `list_tasks` - List tasks with filtering
- `get_task` - Get task details
- `create_task` - Create a new task
- `update_task` - Update task fields
- `delete_task` - Delete/archive a task
- `restore_task` - Restore an archived task

### Lifecycle

- `start_task` - Start working on a task
- `complete_task` - Mark task as completed
- `pause_task` - Pause a task
- `cancel_task` - Cancel a task
- `reopen_task` - Reopen a completed/canceled task

### Queries

- `get_statistics` - Get task statistics
- `get_today_tasks` - Get today's tasks
- `get_week_tasks` - Get this week's tasks
- `get_tag_statistics` - Get tag statistics
- `get_executable_tasks` - Get tasks AI can work on

### Decomposition & Organization

- `decompose_task` - Break down a task into subtasks
- `add_dependency` - Add dependency between tasks
- `remove_dependency` - Remove a dependency
- `set_task_tags` - Set task tags
- `update_task_notes` - Update task notes
- `get_task_notes` - Get task notes

## Usage Examples

Ask Claude Desktop:

- "Show me today's tasks"
- "Create a task to write unit tests for the API"
- "Start task 42"
- "Complete task 42"
- "Decompose task 123 into smaller subtasks for implementing the login feature"
- "What tasks can you execute for me?"

## Requirements

- `taskdog-server` must be running (default: `http://127.0.0.1:8000`)
- Python 3.13+

## Development

```bash
# Install in development mode
cd packages/taskdog-mcp
uv pip install -e .

# Run tests
PYTHONPATH=src uv run python -m pytest tests/ -v
```
