# API Reference

Complete reference for the Taskdog REST API.

## Table of Contents

- [Getting Started](#getting-started)
- [Authentication](#authentication)
- [Base URL](#base-url)
- [Response Format](#response-format)
- [Endpoints](#endpoints)
  - [Documentation](#documentation)
  - [Task Management](#task-management)
  - [Lifecycle Operations](#lifecycle-operations)
  - [Relationships](#relationships)
  - [Notes](#notes)
  - [Analytics](#analytics)
  - [Optimization](#optimization)
  - [Real-time Updates](#real-time-updates)

## Getting Started

The Taskdog API server provides a comprehensive REST API built with FastAPI. All endpoints return JSON and follow REST conventions.

### Starting the Server

```bash
taskdog-server                           # Default: http://127.0.0.1:8000
taskdog-server --host 0.0.0.0            # Bind to all interfaces
taskdog-server --port 3000               # Custom port
taskdog-server --reload                  # Auto-reload for development
taskdog-server --workers 4               # Production with multiple workers
```

### Interactive Documentation

Once the server is running, access interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs` - Interactive API explorer
- **ReDoc**: `http://localhost:8000/redoc` - Alternative documentation format

## Authentication

Taskdog API supports optional API key authentication. When enabled, all HTTP endpoints and WebSocket connections require authentication.

### Configuration

Authentication is configured in `server.toml`:

```toml
# ~/.config/taskdog/server.toml
[auth]
enabled = true  # Enable/disable authentication (default: true)

[[auth.api_keys]]
key = "your-secret-key"
name = "my-tui"  # Friendly name (shown in WebSocket broadcasts)
```

See [examples/server.toml](../examples/server.toml) for a complete example.

### HTTP Authentication

Send API key via `X-Api-Key` header:

```bash
curl -H "X-Api-Key: your-secret-key" http://localhost:8000/api/v1/tasks/
```

### WebSocket Authentication

Send API key via query parameter:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws?token=your-secret-key');
```

### CLI/TUI Configuration

Configure API key in `cli.toml` or environment variable:

```toml
# ~/.config/taskdog/cli.toml
[api]
api_key = "your-secret-key"
```

```bash
export TASKDOG_API_KEY=your-secret-key
```

### Disabling Authentication

For local development or trusted networks, you can disable authentication:

```toml
# ~/.config/taskdog/server.toml
[auth]
enabled = false
```

**Warning:** Only disable authentication in trusted environments.

## Base URL

Default base URL: `http://127.0.0.1:8000`

All API endpoints are prefixed with `/api/v1/` unless otherwise noted.

## Response Format

### Success Response

```json
{
  "id": 1,
  "name": "Task name",
  "status": "pending",
  ...
}
```

### Error Response

```json
{
  "detail": "Error message describing what went wrong"
}
```

HTTP status codes follow REST conventions:

- `200` - Success
- `201` - Created
- `204` - No Content (successful deletion)
- `400` - Bad Request (validation error)
- `404` - Not Found
- `422` - Unprocessable Entity (validation error)
- `500` - Internal Server Error

## Endpoints

### Documentation

#### GET /docs

Interactive Swagger UI documentation

#### GET /redoc

Alternative ReDoc documentation

#### GET /health

Health check endpoint

**Response:**

```json
{
  "status": "healthy"
}
```

### Task Management

Base path: `/api/v1/tasks/`

#### GET /api/v1/tasks/

List tasks with filtering

**Query Parameters:**

- `status` (string, optional) - Filter by status: pending, in_progress, completed, canceled
- `tags` (string[], optional) - Filter by tags (OR logic)
- `start_date` (string, optional) - Filter by planned start date (YYYY-MM-DD)
- `end_date` (string, optional) - Filter by planned end date (YYYY-MM-DD)
- `include_archived` (boolean, optional) - Include archived tasks (default: false)
- `sort_by` (string, optional) - Sort field: id, priority, deadline, name, status, planned_start
- `reverse` (boolean, optional) - Reverse sort order (default: false)

**Response:**

```json
[
  {
    "id": 1,
    "name": "Task name",
    "priority": 100,
    "status": "pending",
    "planned_start": "2025-10-22T09:00:00",
    "planned_end": "2025-10-22T17:00:00",
    "deadline": "2025-10-25T18:00:00",
    "estimated_duration": 16.0,
    "actual_start": null,
    "actual_end": null,
    "is_fixed": false,
    "depends_on": [],
    "daily_allocations": {},
    "tags": ["backend", "api"],
    "is_archived": false
  }
]
```

#### POST /api/v1/tasks/

Create a new task

**Request Body:**

```json
{
  "name": "Task name",
  "priority": 100,
  "estimated_duration": 16.0,
  "deadline": "2025-10-25T18:00:00",
  "is_fixed": false,
  "depends_on": [1, 2],
  "tags": ["backend"]
}
```

**Required fields:** `name`

**Response:** 201 Created with task object

#### GET /api/v1/tasks/{task_id}

Get task details

**Response:** Task object (same structure as list)

#### PATCH /api/v1/tasks/{task_id}

Update task fields

**Request Body:**

```json
{
  "name": "Updated name",
  "priority": 150,
  "deadline": "2025-10-30T18:00:00"
}
```

**Response:** Updated task object

#### DELETE /api/v1/tasks/{task_id}

Delete task

**Query Parameters:**

- `hard` (boolean, optional) - Permanent deletion if true, soft delete if false (default: false)

**Response:** 204 No Content

### Lifecycle Operations

Base path: `/api/v1/tasks/{task_id}/`

#### POST /api/v1/tasks/{task_id}/start

Start a task

Records actual start time and changes status to IN_PROGRESS.

**Response:** Updated task object

#### POST /api/v1/tasks/{task_id}/complete

Complete a task

Records actual end time and changes status to COMPLETED.

**Response:** Updated task object

#### POST /api/v1/tasks/{task_id}/pause

Pause a task

Resets status to PENDING and clears timestamps.

**Response:** Updated task object

#### POST /api/v1/tasks/{task_id}/cancel

Cancel a task

Changes status to CANCELED.

**Response:** Updated task object

#### POST /api/v1/tasks/{task_id}/reopen

Reopen a completed or canceled task

Resets status to PENDING.

**Response:** Updated task object

#### POST /api/v1/tasks/{task_id}/archive

Archive a task (soft delete)

Sets `is_archived` to true. Task can be restored later.

**Response:** 204 No Content

#### POST /api/v1/tasks/{task_id}/restore

Restore an archived task

Sets `is_archived` to false.

**Response:** Updated task object

### Relationships

Base path: `/api/v1/tasks/{task_id}/`

#### POST /api/v1/tasks/{task_id}/dependencies

Add a dependency

**Request Body:**

```json
{
  "depends_on_id": 2
}
```

Creates a dependency: task {task_id} depends on task {depends_on_id}.

**Response:** Updated task object

**Error:** 400 if circular dependency detected

#### DELETE /api/v1/tasks/{task_id}/dependencies/{dep_id}

Remove a dependency

**Response:** Updated task object

#### PUT /api/v1/tasks/{task_id}/tags

Set task tags (replaces existing)

**Request Body:**

```json
{
  "tags": ["backend", "api", "urgent"]
}
```

**Response:** Updated task object

### Notes

Base path: `/api/v1/tasks/{task_id}/notes/`

#### GET /api/v1/tasks/{task_id}/notes

Get task notes

**Response:**

```json
{
  "content": "# Notes\n\nMarkdown content here..."
}
```

#### PUT /api/v1/tasks/{task_id}/notes

Update task notes

**Request Body:**

```json
{
  "content": "# Updated Notes\n\nNew markdown content..."
}
```

**Response:** 204 No Content

#### DELETE /api/v1/tasks/{task_id}/notes

Delete task notes

**Response:** 204 No Content

### Analytics

Base path: `/api/v1/`

#### GET /api/v1/statistics

Get task statistics

**Query Parameters:**

- `period` (string, optional) - all, 7d, 30d (default: all)
- `focus` (string, optional) - all, basic, time, estimation, deadline, priority, trends (default: all)

**Response:**

```json
{
  "total_tasks": 10,
  "by_status": {
    "pending": 5,
    "in_progress": 2,
    "completed": 3,
    "canceled": 0
  },
  "average_duration": 12.5,
  ...
}
```

#### GET /api/v1/gantt

Get Gantt chart data

**Query Parameters:**

- Same filtering options as GET /api/v1/tasks/
- `start_date` (string, optional) - Chart start date
- `end_date` (string, optional) - Chart end date

**Response:**

```json
{
  "tasks": [...],
  "date_range": {
    "start": "2025-10-20",
    "end": "2025-10-30"
  },
  "workload_summary": {
    "2025-10-22": 8.0,
    "2025-10-23": 6.5
  }
}
```

#### GET /api/v1/tags/statistics

Get tag statistics

**Response:**

```json
{
  "backend": 5,
  "api": 3,
  "urgent": 1
}
```

### Optimization

Base path: `/api/v1/`

#### POST /api/v1/optimize

Run schedule optimization

**Request Body:**

```json
{
  "start_date": "2025-10-22",
  "max_hours_per_day": 8.0,
  "algorithm": "greedy",
  "force": false
}
```

**All fields optional:**

- `start_date` - Optimization start date (default: today)
- `max_hours_per_day` - Daily hour limit (default: from config or 6.0)
- `algorithm` - Algorithm to use (default: greedy)
- `force` - Force re-optimization even if tasks already scheduled

**Available algorithms:**

- `greedy` - Schedule highest priority tasks first
- `balanced` - Distribute workload evenly
- `backward` - Schedule from deadline backwards
- `priority_first` - Strict priority ordering
- `earliest_deadline` - Deadline-based scheduling
- `round_robin` - Minimize context switching
- `dependency_aware` - Prioritize blocking tasks
- `genetic` - Genetic algorithm optimization
- `monte_carlo` - Monte Carlo simulation

**Response:**

```json
{
  "scheduled_count": 8,
  "failed_count": 0,
  "workload_summary": {
    "2025-10-22": 8.0,
    "2025-10-23": 6.5
  },
  "failures": []
}
```

#### GET /api/v1/algorithms

List available optimization algorithms

**Response:**

```json
{
  "algorithms": [
    {
      "name": "greedy",
      "description": "Schedule highest priority tasks first"
    },
    ...
  ]
}
```

### Real-time Updates

#### WebSocket /ws

Real-time task notifications

Connect to WebSocket endpoint for real-time updates:

```javascript
// With authentication
const ws = new WebSocket('ws://localhost:8000/ws?token=your-api-key');

// Without authentication (if auth.enabled = false)
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.type);  // task_created, task_updated, task_deleted, task_status_changed
  console.log('Task ID:', data.task_id);
  console.log('Source User:', data.source_user_name);  // Who triggered the event
};
```

**Event types:**

- `task_created` - New task created
- `task_updated` - Task fields updated
- `task_deleted` - Task deleted
- `task_status_changed` - Task status changed
- `schedule_optimized` - Schedule optimization completed

**Event payload:**

All events include `source_user_name` to identify who triggered the event (from API key name).

## Examples

### Create and Schedule a Task

```bash
# 1. Create task
curl -X POST http://localhost:8000/api/v1/tasks/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Implement feature X",
    "priority": 150,
    "estimated_duration": 16.0,
    "deadline": "2025-10-30T18:00:00",
    "tags": ["backend", "feature"]
  }'

# 2. Add dependency
curl -X POST http://localhost:8000/api/v1/tasks/2/dependencies \
  -H "Content-Type: application/json" \
  -d '{"depends_on_id": 1}'

# 3. Run optimization
curl -X POST http://localhost:8000/api/v1/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-10-22",
    "max_hours_per_day": 8.0,
    "algorithm": "balanced"
  }'

# 4. Start task
curl -X POST http://localhost:8000/api/v1/tasks/1/start

# 5. Complete task
curl -X POST http://localhost:8000/api/v1/tasks/1/complete
```

### Filter and Search

```bash
# Get pending tasks with "backend" tag
curl "http://localhost:8000/api/v1/tasks/?status=pending&tags=backend"

# Get tasks in date range
curl "http://localhost:8000/api/v1/tasks/?start_date=2025-10-20&end_date=2025-10-30"

# Get tasks sorted by priority (descending)
curl "http://localhost:8000/api/v1/tasks/?sort_by=priority&reverse=true"

# Include archived tasks
curl "http://localhost:8000/api/v1/tasks/?include_archived=true"
```

### Batch Operations

```bash
# Get multiple tasks and perform operations
TASK_IDS=(1 2 3)

for id in "${TASK_IDS[@]}"; do
  curl -X POST "http://localhost:8000/api/v1/tasks/$id/start"
done
```

## Error Handling

### Common Errors

**404 Not Found**

```json
{
  "detail": "Task with ID 999 not found"
}
```

**400 Bad Request**

```json
{
  "detail": "Cannot start task: Task is already completed"
}
```

**422 Validation Error**

```json
{
  "detail": [
    {
      "loc": ["body", "priority"],
      "msg": "value must be greater than 0",
      "type": "value_error"
    }
  ]
}
```

### Best Practices

1. **Check task existence** before performing operations
2. **Validate status** before state transitions
3. **Handle circular dependencies** when adding dependencies
4. **Use appropriate HTTP methods** (GET for reads, POST/PATCH for writes, DELETE for removal)
5. **Include error handling** in client code
6. **Use query parameters** for filtering and sorting instead of client-side filtering
7. **Leverage WebSocket** for real-time updates in interactive applications

## Rate Limiting

Currently, Taskdog API does not implement rate limiting as it's designed for local use. For production deployments, consider adding rate limiting middleware.
