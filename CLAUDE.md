# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Taskdog is a hierarchical task management CLI tool built with Python, Click, and Rich. It supports parent-child task relationships, time tracking, and multiple task states (PENDING, IN_PROGRESS, COMPLETED, FAILED) with beautiful terminal output.

### Data Storage

Tasks are stored in `tasks.json` following the XDG Base Directory specification:
- Default location: `$XDG_DATA_HOME/taskdog/tasks.json`
- Fallback (if `$XDG_DATA_HOME` not set): `~/.local/share/taskdog/tasks.json`
- The directory is automatically created on first run

## Development Commands

### Testing
```bash
# Run all tests
make test

# Run a single test file
PYTHONPATH=src uv run python -m unittest tests/test_task_service.py

# Run a specific test case
PYTHONPATH=src uv run python -m unittest tests.test_task_service.TaskServiceTest.test_create_task
```

### Installation
```bash
# Install as a CLI tool
make install

# Clean build artifacts
make clean
```

### Running the CLI
```bash
# After installation
taskdog --help

# During development (without installation)
PYTHONPATH=src uv run python -m taskdog.cli --help
```

## Architecture

### Dependency Injection Pattern
The application uses Click's context object for dependency injection (cli.py:28-37). Dependencies are initialized once and stored in `ctx.obj` as a dictionary, making them accessible to all commands via `@click.pass_context`.

### Core Components

**TaskService** (`src/services/task_service.py`)
- Central service layer that coordinates repository and time tracking
- Manages task lifecycle: create, remove (cascade/orphan), update
- Delegates validation to TaskValidator and time tracking to TimeTracker
- Methods: `create_task()`, `remove_cascade()`, `remove_orphan()`, `update_task()`, `update_status()`
- `update_status()` is used by start/done commands for quick status changes with automatic time tracking

**Repository Pattern** (`src/repository/`)
- Abstract interface `TaskRepository` with concrete `JsonTaskRepository` implementation
- Persistence layer for task storage in `tasks.json`
- Responsible for ID generation (`generate_next_id()`)
- Key methods: `get_all()`, `get_by_id()`, `get_children()`, `save()`, `delete()`, `generate_next_id()`

**TimeTracker** (`src/trackers/time_tracker.py`)
- Automatically records `actual_start` when status → IN_PROGRESS
- Automatically records `actual_end` when status → COMPLETED/FAILED
- Invoked by TaskService during status updates

**TaskValidator** (`src/validators/task_validator.py`)
- Validates parent existence before task creation
- Prevents circular parent references by checking ancestor chain
- Raises `TaskNotFoundException` on validation failures

**Command Registration** (`src/taskdog/cli.py`)
- Commands are defined as standalone Click commands using `@click.command()` decorator
- Each command uses `@click.pass_context` to access dependencies from `ctx.obj`
- Commands are registered via `cli.add_command()` in cli.py after imports
- Pattern: Direct command definition with context-based dependency injection
- Commands: add, list, dump, remove, update, start, done, gantt
  - `start <ID>`: Quick command to start a task (sets status to IN_PROGRESS)
  - `done <ID>`: Quick command to complete a task (sets status to COMPLETED)
  - `gantt`: Display tasks as a Gantt chart with timeline visualization

**Rich Formatters** (`src/formatters/`)
- `RichTreeFormatter`: Renders hierarchical task tree with colored status, icons, and indentation (default)
- `RichTableFormatter`: Renders tasks as a beautiful table with borders and column alignment
  - Columns: ID, Name, Priority, Status, Parent, Plan Start, Plan End, Actual Start, Actual End, Deadline, Duration
  - Datetime displayed as `YYYY-MM-DD HH:MM` (seconds omitted for space)
- `RichGanttFormatter`: Renders tasks as a Gantt chart with timeline visualization
  - Shows planned periods (background), actual periods (colored symbols), and deadlines
  - Uses layered rendering: base → planned → actual → deadline (highest priority)
  - Weekend coloring: Saturday (blueish), Sunday (reddish), weekdays (gray)
  - Status-based colors: IN_PROGRESS (blue), COMPLETED (green), FAILED (red)
  - Hierarchical display with date header showing months and days
  - Accessed via `taskdog gantt` command
- Status colors: PENDING (yellow), IN_PROGRESS (blue), COMPLETED (green), FAILED (red)
- Shows task info, datetime fields (deadline, planned, actual), duration estimates
- Format selected with `taskdog list --format [tree|table]` or `-f [tree|table]`

**Custom Click Types** (`src/click_types/`)
- `DateTimeWithDefault`: Extends Click's DateTime type to add default time (18:00:00) when only date is provided
- Accepts formats: `YYYY-MM-DD` (adds 18:00:00) or `YYYY-MM-DD HH:MM:SS` (preserves time)
- Used in add/update commands for date options

### Task Model
**Task** (`src/task/task.py`)
- Core fields: id, name, priority, status, parent_id
- Time fields: planned_start/end, deadline, actual_start/end, estimated_duration
- Auto-calculates `actual_duration_hours` from actual_start/end timestamps
- Datetime format: `YYYY-MM-DD HH:MM:SS`

### Module Structure
All source code lives in `src/` with the following top-level packages:
- `taskdog/` - CLI entry point and context setup
- `task/` - Task model and exceptions
- `commands/` - Click command implementations
- `repository/` - Data persistence layer
- `validators/` - Business rule validation
- `trackers/` - Automatic time tracking
- `formatters/` - Rich-based output formatting
- `services/` - Business logic coordination
- `click_types/` - Custom Click parameter types

### Key Design Decisions
1. **All tests require `PYTHONPATH=src`** - Source modules are not installed during test runs
2. **Commands use Click context** - Dependencies injected via `ctx.obj` dict, accessed with `@click.pass_context`
3. **Command registration via `add_command()`** - Commands imported and registered in `cli.py` via `cli.add_command()`
4. **Repository returns object references** - `save()` updates existing tasks in-place; only adds new tasks to list
5. **Cascade delete vs orphan** - `remove_orphan(id)` orphans children; `remove_cascade(id)` recursively deletes
6. **Repository manages ID generation** - TaskService is stateless; ID generation delegated to Repository
7. **Rich for all output** - Console output uses Rich library for colors, tables, trees, and formatting
8. **Package list in pyproject.toml** - All modules must be explicitly listed in `packages` array for installation
9. **Formatter constants** - Shared constants (STATUS_STYLES, STATUS_COLORS_BOLD, DATETIME_FORMAT) centralized in `formatters/constants.py`
10. **Gantt chart layering** - Timeline visualization applies layers in priority order: empty → planned → actual → deadline
