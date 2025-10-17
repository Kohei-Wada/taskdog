# Taskdog

A personal task management CLI tool with time tracking, schedule optimization, beautiful terminal output, and Gantt chart visualization.

**Note**: Taskdog is designed for individual use. It stores tasks locally and is not intended for team collaboration or multi-user scenarios.

## Features

- **Time Tracking**: Automatic time tracking with planned vs actual duration comparison
- **Schedule Optimization**: Multiple scheduling algorithms to auto-generate optimal task schedules
- **Interactive TUI**: Full-screen Text User Interface with keyboard shortcuts and real-time updates
- **Multiple Task States**: PENDING, IN_PROGRESS, COMPLETED, FAILED, ARCHIVED
- **Beautiful Terminal Output**: Rich formatting with colors and tables
- **Gantt Chart Visualization**: Visual timeline with planned periods, actual progress, deadlines, and workload analysis
- **Flexible Display Options**: Table, Gantt chart, and today view formats
- **Today View**: Quick view of tasks scheduled for today
- **Priority Management**: Set and update task priorities
- **Deadline Support**: Track deadlines with visual indicators
- **Markdown Notes**: Add detailed notes to tasks with editor integration and Rich markdown rendering
- **Batch Operations**: Start, complete, pause, or archive multiple tasks at once
- **Specialized Commands**: Dedicated commands for common updates (deadline, priority, rename, estimate, schedule)

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
# Add tasks
taskdog add "Project Alpha" --priority 200
taskdog add "Design phase" --priority 150
taskdog add "Implementation" --priority 100

# Set deadlines and estimates
taskdog deadline 2 2025-10-20
taskdog deadline 3 2025-10-25
taskdog est 2 16
taskdog est 3 40

# Auto-generate optimal schedule
taskdog optimize

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

# View Gantt chart with workload analysis
taskdog gantt

# Launch interactive TUI for visual task management
taskdog tui
```

## Commands

### `add` - Add a new task

```bash
taskdog add "Task name" [OPTIONS]
```

Options:
- `-p, --priority INTEGER`: Task priority (default: 100, higher value = higher priority)

Creates a new task with minimal information. Use dedicated commands (`deadline`, `est`, `schedule`) to set additional properties after creation.

### `table` - Display tasks in table format

```bash
taskdog table [OPTIONS]
```

Options:
- `-a, --all`: Show all tasks including completed and archived ones (default: hide completed/archived tasks)
- `-s, --sort [id|priority|deadline|name|status|planned_start]`: Sort tasks by specified field (default: id)
- `-r, --reverse`: Reverse sort order

Displays all tasks in a table with columns: ID, Name, Priority, Status, Plan Start, Plan End, Actual Start, Actual End, Deadline, Duration.

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

### `pause` - Pause task(s)

```bash
taskdog pause <TASK_ID> [TASK_ID ...]
```

Pauses task(s) and resets time tracking by setting status back to PENDING. Useful when you need to stop working on a task temporarily. Supports multiple task IDs.

### `done` - Mark task(s) as completed

```bash
taskdog done <TASK_ID> [TASK_ID ...]
```

Sets task status to COMPLETED and records actual end time. Supports multiple task IDs to complete several tasks at once. Shows duration comparison with estimates if available.

### `deadline` - Set task deadline

```bash
taskdog deadline <TASK_ID> <DATE>
```

Sets the task deadline. Date format: `YYYY-MM-DD` (defaults to 18:00:00) or `YYYY-MM-DD HH:MM:SS`.

### `priority` - Set task priority

```bash
taskdog priority <TASK_ID> <PRIORITY>
```

Sets the task priority (higher value = higher priority).

### `rename` - Rename a task

```bash
taskdog rename <TASK_ID> <NAME>
```

Updates the task name.

### `est` - Set estimated duration

```bash
taskdog est <TASK_ID> <HOURS>
```

Sets the estimated duration in hours. Used by the optimize command for schedule generation.

### `schedule` - Set planned schedule

```bash
taskdog schedule <TASK_ID> <START> [END]
```

Sets the planned start and optional end time. Date format: `YYYY-MM-DD` or `YYYY-MM-DD HH:MM:SS`.

### `optimize` - Auto-generate optimal schedules

```bash
taskdog optimize [OPTIONS]
```

Options:
- `--start-date DATE`: Start date for scheduling (default: next weekday)
- `--max-hours-per-day FLOAT`: Maximum work hours per day (default: 6.0)
- `-a, --algorithm NAME`: Optimization algorithm (default: greedy)
  - Available: greedy, balanced, backward, priority_first, earliest_deadline, round_robin, dependency_aware, genetic, monte_carlo
- `-f, --force`: Override existing schedules for all tasks
- `-d, --dry-run`: Preview changes without saving

Auto-generates optimal task schedules based on priorities, deadlines, and workload constraints. Analyzes all tasks with estimated duration and distributes workload across weekdays.

### `archive` - Archive task(s)

```bash
taskdog archive <TASK_ID> [TASK_ID ...]
```

Archives task(s) for data retention. Archived tasks are hidden from default views but preserved in the database. Supports multiple task IDs.

### `rm` - Remove task(s)

```bash
taskdog rm <TASK_ID> [TASK_ID ...]
```

Removes task(s) permanently. Use `archive` instead if you want to preserve task data. Supports multiple task IDs.

### `update` - Update multiple task properties

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

Updates multiple task properties at once. For single-field updates, prefer specialized commands (`deadline`, `priority`, `rename`, `est`, `schedule`).

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

### `tui` - Launch Text User Interface

```bash
taskdog tui
```

Launches an interactive Text User Interface (TUI) for task management with keyboard shortcuts:
- **Navigation**: ↑/↓ arrow keys or j/k (vim-style)
- **Actions**:
  - `a` - Add new task
  - `s` - Start selected task
  - `p` - Pause selected task
  - `d` - Mark task as done
  - `x` - Delete task
  - `i` - Show task details
  - `e` - Edit task
  - `o` - Optimize schedules
  - `O` - Force optimize schedules
  - `r` - Refresh task list
  - `q` - Quit

The TUI provides a full-screen terminal interface with real-time updates and Gantt chart visualization.


## Task States

- **PENDING**: Task not yet started (yellow)
- **IN_PROGRESS**: Task is being worked on (blue)
- **COMPLETED**: Task successfully finished (green)
- **FAILED**: Task failed or cancelled (red)
- **ARCHIVED**: Task archived for data retention (hidden from default views)

## Data Storage

Tasks are stored in JSON format following the XDG Base Directory specification:
- Default: `$XDG_DATA_HOME/taskdog/tasks.json`
- Fallback: `~/.local/share/taskdog/tasks.json`

The directory is created automatically on first run.

## Design Philosophy

Taskdog focuses on **smart task management with automated scheduling**:

- **Estimate durations**: Set realistic time estimates for tasks
- **Set priorities and deadlines**: Help the optimizer make smart decisions
- **Let the optimizer work**: Use `taskdog optimize` to auto-generate optimal schedules
- **Track progress**: Monitor actual vs planned time to improve future estimates
- **Review regularly**: Use `taskdog today` and `taskdog gantt` to stay on track

### Best Practices

- **Keep tasks focused**: Break large tasks into smaller, manageable pieces (under 4-8 hours)
- **Estimate accurately**: Use past actual durations to improve future estimates
- **Set realistic deadlines**: Allow buffer time for unexpected issues
- **Use priorities**: Higher priority tasks get scheduled earlier
- **Review and adjust**: Re-run `optimize` when priorities or deadlines change

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
      presentation/                 # Presentation layer (CLI, renderers, TUI)
         cli/commands/              # Click command implementations
         renderers/                 # Rich-based output formatting
         tui/                       # Text User Interface (Textual)
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
- **Presentation Layer** (`presentation/`): CLI commands, Rich-based renderers for terminal output, and Textual-based TUI
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
