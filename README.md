# Taskdog

A personal hierarchical task management CLI tool with time tracking, beautiful terminal output, and Gantt chart visualization.

**Note**: Taskdog is designed for individual use. It stores tasks locally and is not intended for team collaboration or multi-user scenarios.

## Features

- **Hierarchical Task Management**: Create parent-child task relationships to organize complex projects
- **Time Tracking**: Automatic time tracking with planned vs actual duration comparison
- **Multiple Task States**: PENDING, IN_PROGRESS, COMPLETED, FAILED
- **Beautiful Terminal Output**: Rich formatting with colors, tables, and tree views
- **Gantt Chart Visualization**: Visual timeline with planned periods, actual progress, and deadlines
- **Flexible Display Options**: Tree, table, and Gantt chart formats
- **Today View**: Quick view of tasks scheduled for today
- **Priority Management**: Set and update task priorities
- **Deadline Support**: Track deadlines with visual indicators
- **Markdown Notes**: Add detailed notes to tasks with editor integration and Rich markdown rendering
- **Batch Operations**: Start or complete multiple tasks at once

## Installation

```bash
# Clone the repository
git clone https://github.com/Kohei-Wada/taskdog.git
cd taskdog

# Install using Make
make install
```

## Quick Start

```bash
# Add a root task
taskdog add --name "Project Alpha" --priority 1

# Add a subtask (assuming parent task ID is 1)
taskdog add 1 --name "Design phase" --planned-start 2025-10-15 --planned-end 2025-10-20

# Add another subtask with deadline
taskdog add 1 --name "Implementation" --deadline 2025-10-25 --estimated-duration 40

# View tasks in tree format
taskdog tree

# View tasks in table format
taskdog table

# View tasks scheduled for today
taskdog today

# Start working on a task
taskdog start 2

# Start multiple tasks at once
taskdog start 2 3 4

# Complete a task
taskdog done 2

# Complete multiple tasks at once
taskdog done 2 3 4

# Add notes to a task (opens editor)
taskdog note 2

# View task details with notes
taskdog show 2

# View Gantt chart
taskdog gantt
```

## Commands

### `add` - Add a new task

```bash
taskdog add [PARENT_ID] --name "Task name" [OPTIONS]
```

Options:
- `--name TEXT`: Task name (required)
- `--priority INTEGER`: Task priority (default: 0)
- `--planned-start DATETIME`: Planned start time (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
- `--planned-end DATETIME`: Planned end time (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
- `--deadline DATETIME`: Task deadline (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
- `--estimated-duration FLOAT`: Estimated duration in hours

**Note**: When you provide a date without time (e.g., `2025-10-15`), it defaults to 18:00:00.

### `tree` - Display tasks in hierarchical tree format

```bash
taskdog tree [OPTIONS]
```

Options:
- `-a, --all`: Show all tasks including completed ones (default: hide completed tasks)

Displays tasks in a hierarchical tree with colored status indicators and task details.

### `table` - Display tasks in flat table format

```bash
taskdog table [OPTIONS]
```

Options:
- `-a, --all`: Show all tasks including completed ones (default: hide completed tasks)

Displays all tasks in a table with columns: ID, Name, Priority, Status, Parent, Plan Start, Plan End, Actual Start, Actual End, Deadline, Duration.

### `today` - Display tasks for today

```bash
taskdog today
```

Shows tasks that:
- Have a deadline today
- Are planned to start or end today
- Are currently in progress

### `gantt` - Display Gantt chart

```bash
taskdog gantt
```

Visualizes tasks on a timeline showing:
- **Planned periods**: Daily allocated hours displayed as numbers (e.g., `4`, `2.5`) with background shading
- **Actual progress**:
  - IN_PROGRESS tasks: Blue `◆` symbols from actual_start to today
  - COMPLETED tasks: Green `◆` symbols from actual_start to actual_end
- **Deadlines**: Red `◆` symbol on deadline date
- **Workload summary**: Row at bottom showing total daily hours with color-coded warnings (green ≤6h, yellow ≤8h, red >8h)
- **Weekend coloring**: Saturday (blueish) and Sunday (reddish) highlighted

### `start` - Start working on task(s)

```bash
taskdog start <TASK_ID> [TASK_ID ...]
```

Sets task status to IN_PROGRESS and records actual start time. Supports multiple task IDs to start several tasks at once.

### `done` - Mark task(s) as completed

```bash
taskdog done <TASK_ID> [TASK_ID ...]
```

Sets task status to COMPLETED and records actual end time. Supports multiple task IDs to complete several tasks at once. Shows duration comparison with estimates if available.

### `update` - Update task properties

```bash
taskdog update <TASK_ID> [OPTIONS]
```

Options:
- `--name TEXT`: Update task name
- `--priority INTEGER`: Update priority
- `--status [PENDING|IN_PROGRESS|COMPLETED|FAILED]`: Update status
- `--planned-start DATETIME`: Update planned start
- `--planned-end DATETIME`: Update planned end
- `--deadline DATETIME`: Update deadline
- `--estimated-duration FLOAT`: Update estimated duration

### `remove` - Remove a task

```bash
taskdog remove <TASK_ID> [OPTIONS]
```

Options:
- `--cascade`: Delete task and all its children recursively

Default behavior: orphan children (set their parent_id to None).

### `note` - Edit task notes

```bash
taskdog note <TASK_ID>
```

Opens the task's markdown notes in your editor ($EDITOR environment variable, defaults to vim/nano/vi). Creates a template if the notes file doesn't exist. Notes are stored at `$XDG_DATA_HOME/taskdog/notes/{task_id}.md`.

### `show` - Display task details

```bash
taskdog show <TASK_ID> [OPTIONS]
```

Options:
- `--raw`: Show raw markdown instead of rendered notes

Displays detailed task information including all fields and renders markdown notes with Rich formatting.

### `export` - Export tasks to various formats

```bash
taskdog export [OPTIONS]
```

Options:
- `--format [json]`: Output format (default: json). More formats (CSV, Markdown, iCalendar) coming soon.
- `--output, -o PATH`: Output file path (default: stdout)

Exports all tasks in the specified format. Currently supports JSON format only.

Examples:
```bash
# Print JSON to stdout
taskdog export

# Save JSON to file
taskdog export -o tasks.json

# Explicit format specification
taskdog export --format json -o backup.json
```


## Task States

- **PENDING**: Task not yet started (yellow)
- **IN_PROGRESS**: Task is being worked on (blue)
- **COMPLETED**: Task successfully finished (green)
- **FAILED**: Task failed or cancelled (red)

## Data Storage

Tasks are stored in JSON format following the XDG Base Directory specification:
- Default: `$XDG_DATA_HOME/taskdog/tasks.json`
- Fallback: `~/.local/share/taskdog/tasks.json`

The directory is created automatically on first run.

## Development

### Requirements

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (Python package installer)

### Running Tests

```bash
# Run all tests
make test

# Run a specific test file
PYTHONPATH=src uv run python -m unittest tests/test_create_task_use_case.py

# Run a specific test case
PYTHONPATH=src uv run python -m unittest tests.test_create_task_use_case.CreateTaskUseCaseTest.test_execute_success
```

### Running CLI During Development

```bash
# Without installation
PYTHONPATH=src uv run python -m taskdog.cli --help
```

### Project Structure

```
taskdog/
   src/
      taskdog/                      # CLI entry point
      domain/                       # Domain layer (entities, services, exceptions)
         entities/                  # Core business entities (Task)
         services/                  # Domain services (TimeTracker)
         exceptions/                # Domain exceptions
      application/                  # Application layer (use cases, queries, DTOs)
         use_cases/                 # Business logic orchestration
         queries/                   # Read-optimized operations
         dto/                       # Data Transfer Objects
      infrastructure/               # Infrastructure layer (persistence)
         persistence/               # Repository implementations
      presentation/                 # Presentation layer (CLI, formatters)
         cli/commands/              # Click command implementations
         formatters/                # Rich-based output formatting
      shared/                       # Shared utilities
         click_types/               # Custom Click parameter types
      utils/                        # Utility functions
   tests/                           # Unit tests
   pyproject.toml                   # Project configuration
   Makefile                         # Build and test commands
   README.md                        # This file

```

## Architecture

Taskdog follows **Clean Architecture** principles with clear separation of concerns:

- **Domain Layer** (`domain/`): Core business entities (Task), domain services (TimeTracker), and exceptions
- **Application Layer** (`application/`): Use cases for business operations, query services for reads, and DTOs for data transfer
- **Infrastructure Layer** (`infrastructure/`): Repository implementations for data persistence
- **Presentation Layer** (`presentation/`): CLI commands and Rich-based formatters for terminal output
- **Shared Layer** (`shared/`): Cross-cutting utilities like custom Click types

**Key Patterns:**
- **Use Case Pattern**: Each business operation (create, start, complete, update, remove) is encapsulated in a dedicated use case
- **Repository Pattern**: Abstract interface with concrete JSON implementation for data persistence
- **Dependency Injection**: Dependencies initialized in `cli.py` and injected via Click's context object
- **CQRS-like Separation**: Use cases handle writes, QueryService handles reads with filters and sorters

See [CLAUDE.md](CLAUDE.md) for detailed architecture documentation.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.
