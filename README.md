# Taskdog

A task management system with CLI/TUI interfaces and REST API server, featuring time tracking, schedule optimization, and beautiful terminal output.

**Architecture**: UV workspace monorepo with three packages:
- **taskdog-core**: Core business logic and SQLite persistence
- **taskdog-server**: FastAPI REST API server
- **taskdog-ui**: CLI and TUI interfaces

**Note**: Designed for individual use. Stores tasks locally in SQLite database.

## Features

- **REST API Server**: FastAPI-based server with automatic OpenAPI documentation
- **Multiple Interfaces**: CLI commands, full-screen TUI, and HTTP API
- **Schedule Optimization**: 9 algorithms to auto-generate optimal schedules (respects fixed tasks & dependencies)
- **Fixed Tasks**: Mark tasks as fixed to prevent rescheduling (e.g., meetings)
- **Task Dependencies**: Define dependencies with circular detection
- **Interactive TUI**: Full-screen interface with keyboard shortcuts
- **Time Tracking**: Automatic tracking with planned vs actual comparison
- **Gantt Chart**: Visual timeline with workload analysis
- **Markdown Notes**: Editor integration with Rich rendering
- **Batch Operations**: Start/complete/pause/cancel multiple tasks at once
- **Soft Delete**: Restore removed tasks
- **SQLite Storage**: Transactional persistence with ACID guarantees

## Installation

**Requirements**: Python 3.11+ (3.13+ for individual packages), [uv](https://github.com/astral-sh/uv)

```bash
# Clone the repository
git clone https://github.com/Kohei-Wada/taskdog.git
cd taskdog

# Install globally (recommended - installs taskdog and taskdog-server commands)
make install

# OR: Install with development dependencies (for contributing)
make install-dev

# OR: Install locally for development (editable mode)
make install-local
```

**What gets installed:**
- `taskdog` - CLI and TUI interface
- `taskdog-server` - FastAPI REST API server

**Common Make targets:**
```bash
make install          # Install as global commands via uv tool
make install-dev      # Install all packages with dev dependencies
make install-local    # Install locally for development (per-package)
make reinstall        # Clean and reinstall
make uninstall        # Remove global installations
```

## Quick Start

### CLI Usage

```bash
# Add tasks with priorities and estimates
taskdog add "Design phase" -p 150
taskdog add "Implementation" -p 100
taskdog deadline 1 2025-10-20
taskdog est 1 16

# Add fixed task (won't be rescheduled)
taskdog add "Team meeting" --fixed
taskdog schedule 2 "2025-10-22 10:00" "2025-10-22 11:00"

# Add dependencies and optimize
taskdog add-dependency 2 1          # Task 2 depends on task 1
taskdog optimize                    # Auto-generate schedule

# Manage tasks
taskdog start 1                     # Start task
taskdog done 1                      # Complete task
taskdog start 2 3 4                 # Batch operations
taskdog note 1                      # Edit notes

# Visualize
taskdog table                       # Table view
taskdog gantt                       # Gantt chart
taskdog today                       # Today's tasks
taskdog tui                         # Interactive TUI
```

### API Server Usage

```bash
# Start the server
taskdog-server                      # Default: http://127.0.0.1:8000

# With custom configuration
taskdog-server --host 0.0.0.0 --port 3000 --reload

# Access API documentation
# Open http://localhost:8000/docs in your browser
```

**API Examples:**
```bash
# Create task via API
curl -X POST http://localhost:8000/api/v1/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"name": "API Task", "priority": 100}'

# List tasks
curl http://localhost:8000/api/v1/tasks/

# Start task
curl -X POST http://localhost:8000/api/v1/tasks/1/lifecycle/start

# Get Gantt data
curl http://localhost:8000/api/v1/analytics/gantt
```

## Interactive TUI

Taskdog includes a full-screen terminal user interface (TUI) for managing tasks interactively.

![TUI Screenshot](docs/images/TaskdogTUI_half.svg)

**Features:**
- Real-time task search and filtering
- Keyboard shortcuts for quick operations
- Sort by deadline, priority, planned start, or ID
- Visual status indicators with colors
- Task details panel with dependencies

**Keyboard Shortcuts:**
- `a` - Add new task
- `s` - Start selected task
- `P` - Pause selected task
- `d` - Complete (done) selected task
- `c` - Cancel selected task
- `R` - Reopen task
- `x` - Archive task (soft delete)
- `X` - Hard delete task (permanent)
- `i` - Show task details
- `e` - Edit task
- `v` - Edit task note
- `t` - Toggle visibility of completed/canceled tasks
- `o` - Run optimizer
- `r` - Refresh task list
- `S` - Sort selection dialog (deadline/planned_start/priority/estimated_duration/id)
- `/` - Focus search box
- `Escape` - Clear/hide search
- `q` - Quit

Launch the TUI with:
```bash
taskdog tui
```

## API Server

The FastAPI server provides a comprehensive REST API for all task management operations.

### Starting the Server

```bash
taskdog-server                           # Default: http://127.0.0.1:8000
taskdog-server --host 0.0.0.0            # Bind to all interfaces
taskdog-server --port 3000               # Custom port
taskdog-server --reload                  # Auto-reload for development
taskdog-server --workers 4               # Production with multiple workers
```

### API Endpoints

**Documentation:**
- `GET /docs` - Interactive Swagger UI (OpenAPI documentation)
- `GET /redoc` - Alternative ReDoc documentation
- `GET /health` - Health check endpoint

**Task Management** (`/api/v1/tasks/`):
- `GET /api/v1/tasks/` - List tasks with filtering (status, tags, date ranges, archived)
- `POST /api/v1/tasks/` - Create new task
- `GET /api/v1/tasks/{task_id}` - Get task details
- `PATCH /api/v1/tasks/{task_id}` - Update task fields
- `DELETE /api/v1/tasks/{task_id}` - Delete task (soft by default, `?hard=true` for permanent)

**Lifecycle Operations** (`/api/v1/tasks/{task_id}/lifecycle/`):
- `POST .../start` - Start task
- `POST .../complete` - Complete task
- `POST .../pause` - Pause task (reset to PENDING)
- `POST .../cancel` - Cancel task
- `POST .../reopen` - Reopen completed/canceled task
- `POST .../restore` - Restore archived task
- `POST .../log-hours` - Log actual hours worked

**Relationships** (`/api/v1/tasks/{task_id}/`):
- `POST .../dependencies` - Add dependency
- `DELETE .../dependencies/{dep_id}` - Remove dependency
- `GET .../tags` - Get task tags
- `PUT .../tags` - Set task tags (replaces existing)

**Notes** (`/api/v1/tasks/{task_id}/notes/`):
- `GET .../notes` - Get task notes (markdown)
- `PUT .../notes` - Update task notes

**Analytics** (`/api/v1/analytics/`):
- `GET .../stats` - Task statistics (period, focus filters)
- `GET .../gantt` - Gantt chart data (date ranges, filters)
- `GET .../tags` - Tag statistics

**Optimization** (`/api/v1/optimize/`):
- `POST .../schedule` - Run schedule optimization with algorithm selection

All endpoints return JSON with proper HTTP status codes. See `/docs` for detailed schemas and interactive testing.

## Commands

### Core Commands

**Task Creation & Updates**
- `add "Task name" [-p PRIORITY] [--fixed] [-d DEP_ID] [-t TAG]` - Create task (multiple -d and -t allowed)
- `deadline ID DATE` - Set deadline (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
- `priority ID N` - Set priority (higher = more important)
- `est ID HOURS` - Set estimated duration
- `schedule ID START [END]` - Set planned schedule
- `rename ID NAME` - Rename task
- `update ID [--name] [--priority] [--status] [--planned-start] [--planned-end] [--deadline] [--estimated-duration]` - Multi-field update

**Task Management**
- `start ID...` - Start tasks (records actual start time)
- `done ID...` - Complete tasks (records actual end time)
- `pause ID...` - Pause tasks (reset to PENDING)
- `cancel ID...` - Cancel tasks
- `reopen ID...` - Reopen completed/canceled tasks
- `rm ID... [--hard]` - Remove tasks (soft delete by default)
- `restore ID...` - Restore soft-deleted tasks

**Dependencies**
- `add-dependency TASK_ID DEP_ID` - Add dependency (circular detection)
- `remove-dependency TASK_ID DEP_ID` - Remove dependency

**Tags Management**
- `tags` - List all tags with counts
- `tags ID` - Show tags for a task
- `tags ID TAG1 TAG2...` - Set tags for a task (replaces existing)

**Time Tracking**
- `log-hours ID HOURS [-d DATE]` - Log actual hours worked (default: today)

**Optimization**
- `optimize [--start-date DATE] [--max-hours-per-day N] [-a ALGORITHM] [-f]`
  - Algorithms: greedy (default), balanced, backward, priority_first, earliest_deadline, round_robin, dependency_aware, genetic, monte_carlo
  - Respects fixed tasks and dependencies
  - Distributes workload across weekdays

**Visualization**
- `table` - Table view with extensive options (shows non-archived tasks by default):
  - Sort: `-s/--sort` (id, priority, deadline, name, status, planned_start)
  - Filter: `--status` (pending, in_progress, completed, canceled), `-t/--tag`, `--start-date`, `--end-date`
  - Display: `-a/--all` (include archived), `-r/--reverse`, `-f/--fields` (custom field selection)
- `gantt` - Gantt chart with workload analysis (shows non-archived tasks by default):
  - Same filter/sort options as table (default sort: deadline)
- `today` - Today's tasks (deadline today, planned includes today, or IN_PROGRESS)
- `week` - This week's tasks (same filtering logic as today)
- `show ID [--raw]` - Task details + notes (markdown rendered or raw)
- `export` - Export tasks (exports non-archived tasks by default):
  - Format: `--format` (json [default] or csv)
  - Output: `-o/--output FILE`
  - Fields: `-f/--fields` (custom field selection)
  - Filters: Same as table (--all, --status, --tag, --start-date, --end-date)

**Analytics**
- `stats` - Task statistics and analytics:
  - Period: `-p/--period` (all [default], 7d, 30d)
  - Focus: `-f/--focus` (all [default], basic, time, estimation, deadline, priority, trends)

**Notes & TUI**
- `note ID` - Edit markdown notes ($EDITOR)
- `tui` - Interactive TUI
  - See Interactive TUI section above for full keyboard shortcuts
  - Search: `/` to search, `Escape` to clear
  - Sort: `S` for sort dialog (deadline/planned_start/priority/estimated_duration/id)


## Task States

- **PENDING**: Not started (yellow)
- **IN_PROGRESS**: Being worked on (blue)
- **COMPLETED**: Finished (green)
- **CANCELED**: Won't be done (red)

**Note**: Archived tasks (soft-deleted) retain their original status and can be restored with `taskdog restore`.

## Tags

Tasks can be organized with tags for better categorization and filtering.

```bash
# Add task with tags
taskdog add "Backend API" --tag backend --tag api

# Manage tags
taskdog tags                    # List all tags with counts
taskdog tags 1                  # Show tags for task 1
taskdog tags 1 urgent backend   # Set tags (replaces existing)

# Filter by tags
taskdog table --tag backend     # Show tasks with 'backend' tag
taskdog table --tag api --tag db  # OR logic: tasks with 'api' OR 'db'
```

## Data Storage

**Tasks**: SQLite database at `$XDG_DATA_HOME/taskdog/tasks.db` (fallback: `~/.local/share/taskdog/tasks.db`)
- Transactional writes with ACID guarantees
- Automatic rollback on errors
- Indexed queries for efficient filtering
- Connection pooling and proper resource management

**Config**: `$XDG_CONFIG_HOME/taskdog/config.toml` (fallback: `~/.config/taskdog/config.toml`)

### Configuration

Optional TOML configuration file with the following sections:

```toml
[optimization]
max_hours_per_day = 6.0        # Default work hours per day (default: 6.0)
default_algorithm = "greedy"   # Default scheduling algorithm (default: "greedy")

[task]
default_priority = 5           # Default task priority (default: 5)

[display]
datetime_format = "%Y-%m-%d %H:%M:%S"  # Datetime display format

[time]
default_start_hour = 9         # Business day start hour (default: 9)
default_end_hour = 18          # Business day end hour (default: 18)

[region]
country = "JP"                 # ISO 3166-1 alpha-2 country code for holiday checking
                               # Examples: "JP", "US", "GB", "DE"
                               # Default: None (no holiday checking)
```

**Priority**: CLI arguments > Config file > Defaults

## Workflow

1. **Create tasks** with priorities and estimates
2. **Set deadlines** and dependencies
3. **Run optimizer** to auto-generate schedules
4. **Track progress** with start/done commands
5. **Review** with `today` and `gantt` commands

## Development

**Requirements**: Python 3.11+ (workspace root), Python 3.13+ (individual packages), [uv](https://github.com/astral-sh/uv)

### Development Commands

```bash
# Installation
make install-dev                    # Install all packages with dev dependencies
make install-local                  # Install locally for development (editable mode)
make install                        # Install as global commands

# Testing
make test                           # All tests (core + server + ui)
make test-core                      # Core package tests only
make test-server                    # Server package tests only
make test-ui                        # UI package tests only

# Single test file (from package directory)
cd packages/taskdog-core && PYTHONPATH=src uv run python -m unittest tests/test_module.py
cd packages/taskdog-ui && PYTHONPATH=src uv run python -m unittest tests/test_module.py

# Code Quality
make lint                           # Ruff linter on all packages
make format                         # Ruff formatter + auto-fix
make typecheck                      # mypy type checking (progressive, Phase 4)
make check                          # lint + typecheck

# Cleanup
make clean                          # Clean build artifacts and cache
make uninstall                      # Uninstall global commands
make reinstall                      # Clean + reinstall

# Run during development (without installation)
cd packages/taskdog-ui && PYTHONPATH=src uv run python -m taskdog.cli_main --help
cd packages/taskdog-server && PYTHONPATH=src uv run python -m taskdog_server.main --help
```

### Monorepo Structure

The project uses UV workspace with three packages:

```
taskdog/
├── packages/
│   ├── taskdog-core/      # Core business logic
│   │   ├── src/taskdog_core/
│   │   │   ├── domain/           # Entities, services, exceptions
│   │   │   ├── application/      # Use cases, queries, DTOs, validators
│   │   │   ├── infrastructure/   # SQLite repository, config
│   │   │   └── controllers/      # TaskController, QueryController
│   │   └── tests/
│   ├── taskdog-server/    # FastAPI REST API
│   │   ├── src/taskdog_server/
│   │   │   ├── api/              # Routers, models, dependencies
│   │   │   └── main.py           # FastAPI application
│   │   └── tests/
│   └── taskdog-ui/        # CLI and TUI
│       ├── src/taskdog/
│       │   ├── cli/              # Click commands
│       │   ├── tui/              # Textual TUI
│       │   ├── console/          # Output formatters
│       │   └── renderers/        # Table and Gantt renderers
│       └── tests/
├── pyproject.toml         # Workspace configuration
└── Makefile              # Build and test automation
```

**Package Dependencies:**
- `taskdog-server` depends on `taskdog-core`
- `taskdog-ui` depends on `taskdog-core`
- `taskdog-core` has no dependencies on other packages (pure business logic)

### Architecture

**Clean Architecture** with 5 layers across three packages:

**Domain** (taskdog-core):
- Entities (Task, TaskStatus)
- Services (TimeTracker)
- Exceptions (TaskNotFoundException, TaskValidationError, etc.)

**Application** (taskdog-core):
- Use cases (CreateTaskUseCase, StartTaskUseCase, OptimizeScheduleUseCase, etc.)
- Queries (TaskQueryService, WorkloadCalculator - CQRS pattern)
- DTOs (Request/Response objects)
- Validators (Field validation with Strategy Pattern)
- Optimization strategies (9 algorithms with StrategyFactory)

**Infrastructure** (taskdog-core):
- Repository (SqliteTaskRepository with transactional writes)
- Persistence mappers (TaskDbMapper)
- Config (ConfigManager for TOML config)

**Controllers** (taskdog-core):
- TaskController: Orchestrates write operations (commands)
- QueryController: Orchestrates read operations (queries)
- Shared across all presentation layers (CLI, TUI, API)

**Presentation** (taskdog-server + taskdog-ui):
- **Server**: FastAPI routers, Pydantic models, API dependencies
- **UI**: Click CLI commands, Textual TUI, Rich renderers, console writers

**Shared** (across packages):
- Cross-cutting utilities (XDG paths, date utils)

**Key Patterns**:
- Use Case (each business operation)
- Repository (data persistence abstraction)
- CQRS (separate read/write paths via TaskController and QueryController)
- Dependency Injection (CliContext, TUIContext, ApiContext)
- Template Method (StatusChangeUseCase)
- Strategy (Optimization algorithms, field validators)
- Command (TUI command pattern with registry)

See [CLAUDE.md](CLAUDE.md) for detailed architecture documentation.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.
