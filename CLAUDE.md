# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Taskdog is a task management CLI tool built with Python, Click, and Rich. It supports time tracking, multiple task states (PENDING, IN_PROGRESS, COMPLETED, FAILED, ARCHIVED), and schedule optimization with beautiful terminal output. The codebase follows Clean Architecture principles with clear separation between layers.

### Data Storage

Tasks are stored in `tasks.json` following the XDG Base Directory specification:
- Default location: `$XDG_DATA_HOME/taskdog/tasks.json`
- Fallback (if `$XDG_DATA_HOME` not set): `~/.local/share/taskdog/tasks.json`
- The directory is automatically created on first run

## Development Commands

### Setup
```bash
# Install package in editable mode (required for development)
uv pip install -e .

# Or install with development dependencies
uv pip install -e ".[dev]"
```

### Testing
```bash
# Run all tests
make test

# Run a single test file
uv run python -m unittest tests/test_create_task_use_case.py

# Run a specific test case
uv run python -m unittest tests.test_create_task_use_case.CreateTaskUseCaseTest.test_execute_success
```

### Code Quality
```bash
# Lint code with ruff
make lint

# Format code with ruff
make format

# Type check with mypy
make typecheck

# Run both lint and typecheck
make check
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

The application follows **Clean Architecture** with distinct layers:

### Layer Structure

**Domain Layer** (`src/domain/`)
- `entities/`: Core business entities (Task, TaskStatus)
- `services/`: Domain services (TimeTracker, WorkloadCalculator)
  - `TimeTracker`: Records actual_start and actual_end timestamps during status transitions
  - `WorkloadCalculator`: Computes daily hours from task allocations or evenly distributes estimated duration
- `exceptions/`: Domain-specific exceptions
  - `TaskNotFoundException`: Task with given ID not found
  - `TaskValidationError`: Base exception for validation failures
  - `TaskAlreadyFinishedError`: Trying to start already finished task
  - `TaskNotStartedError`: Trying to complete task that hasn't been started
- No dependencies on other layers; defines core business logic

**Application Layer** (`src/application/`)
- `use_cases/`: Business logic orchestration (CreateTaskUseCase, StartTaskUseCase, OptimizeScheduleUseCase, ArchiveTaskUseCase, etc.)
  - Each use case inherits from base class with `execute(input_dto)` method
  - Use cases are stateless and dependency-injected
- `validators/`: Field-specific validation logic using Strategy Pattern + Registry
  - `FieldValidator`: Abstract base class for all field validators
    - Defines uniform interface: `validate(value, task, repository)`
  - `TaskFieldValidatorRegistry`: Central registry managing field validators
    - Auto-registers validators on initialization
    - Validates fields by name: `validate_field(field_name, value, task)`
    - Extensible design: adding new validators requires 3 steps (create validator class, register in registry, done)
  - **Field Validators**:
    - `StatusValidator`: Validates status transitions (raises `TaskNotStartedError`, `TaskAlreadyFinishedError`, etc.)
  - Used by UpdateTaskUseCase to validate field updates before applying changes
  - All validators use custom domain exceptions for consistent error handling
- `services/`: Application services that coordinate complex operations
  - `WorkloadAllocator`: Distributes task hours across weekdays respecting max hours/day
  - `OptimizationSummaryBuilder`: Builds summary reports for schedule optimization
  - `optimization/`: Multiple scheduling algorithms implementing the Strategy pattern
    - `GreedyOptimizationStrategy`: Front-loads tasks (default)
    - `BalancedOptimizationStrategy`: Even workload distribution
    - `BackwardOptimizationStrategy`: Just-in-time scheduling from deadlines
    - `PriorityFirstOptimizationStrategy`: Priority-based scheduling only
    - `EarliestDeadlineOptimizationStrategy`: Earliest Deadline First (EDF)
    - `RoundRobinOptimizationStrategy`: Parallel progress on multiple tasks
    - `DependencyAwareOptimizationStrategy`: Critical Path Method (CPM)
    - `GeneticOptimizationStrategy`: Evolutionary algorithm
    - `MonteCarloOptimizationStrategy`: Random sampling approach
    - `StrategyFactory`: Factory for creating strategy instances
- `sorters/`: Task sorting components
  - `TaskSorter`: General-purpose sorter for user-facing queries (supports sorting by id, priority, deadline, name, status, planned_start)
  - `OptimizationTaskSorter`: Specialized sorter for schedule optimization (sorts by deadline urgency, priority field, and task ID)
- `queries/`: Read-optimized operations (TaskQueryService with filters and sorters)
- `dto/`: Data Transfer Objects for use case inputs (CreateTaskInput, StartTaskInput, UpdateTaskInput, etc.)
- Depends on domain layer; defines application-specific logic

**Infrastructure Layer** (`src/infrastructure/`)
- `persistence/`: Repository implementations (TaskRepository abstract, JsonTaskRepository concrete)
- Provides concrete implementations of interfaces defined in domain/application
- Handles external concerns (file I/O, data persistence)

**Presentation Layer** (`src/presentation/`)
- `cli/commands/`: Click command implementations (add, tree, table, gantt, start, done, optimize, archive, etc.)
- `cli/context.py`: CliContext dataclass for dependency injection (console, repository, time_tracker)
- `cli/error_handler.py`: Decorators for consistent error handling
- `formatters/`: Rich-based output formatting (RichTreeFormatter, RichTableFormatter, RichGanttFormatter, RichOptimizationFormatter)
- Depends on application layer use cases and queries

**Shared Layer** (`src/shared/`)
- `click_types/`: Custom Click parameter types (DateTimeWithDefault)
- Cross-cutting utilities used across layers

### Dependency Injection Pattern

Dependencies are managed through Click's context object using the `CliContext` dataclass:

**CliContext** (`src/presentation/cli/context.py`):
- Dataclass containing shared dependencies: `console`, `repository`, `time_tracker`
- Initialized in `cli.py` and passed to all commands via `ctx.obj`
- Commands access via `ctx.obj: CliContext` type annotation

**Local instantiation in commands**:
- Use cases are created locally in each command function (e.g., `CreateTaskUseCase(repository)`)
- `TaskQueryService` is instantiated locally in query commands
- Formatters are instantiated locally per command
- Application services (EstimatedDurationPropagator, SchedulePropagator, etc.) instantiated as needed

### Core Components

**Use Cases** (`src/application/use_cases/`)
- Generic base class: `UseCase[TInput, TOutput]` with abstract `execute(input_dto)` method
- Concrete implementations: CreateTaskUseCase, StartTaskUseCase, CompleteTaskUseCase, UpdateTaskUseCase, RemoveTaskUseCase, ArchiveTaskUseCase, OptimizeScheduleUseCase
- Each use case encapsulates a single business operation
- Use cases validate inputs, orchestrate domain logic, and coordinate with repository/services

**Query Service** (`src/application/queries/task_query_service.py`)
- Read-only operations optimized for data retrieval
- Methods: `get_today_tasks()`, `get_all_tasks()`, `get_incomplete_tasks()`
  - All methods support `sort_by` and `reverse` parameters for flexible sorting
  - Sort keys: `id`, `priority`, `deadline`, `name`, `status`, `planned_start`
- Uses filters (TodayFilter) and sorters (TaskSorter) for query composition
- Separates reads from writes (CQRS-like pattern)

**Task Sorters** (`src/application/sorters/`)
Two specialized sorters with distinct responsibilities:

**TaskSorter** - General-purpose sorting for user-facing queries
- Provides flexible sorting functionality for task lists
- Supports multiple sort keys: `id`, `priority`, `deadline`, `name`, `status`, `planned_start`
- Default behaviors:
  - `priority`: Descending by default (higher priority first)
  - Other keys: Ascending by default
  - None values: Sorted last for date/time fields
- `reverse` parameter inverts sort order
- Used by TaskQueryService for table, gantt, and today commands

**OptimizationTaskSorter** - Specialized sorting for schedule optimization
- Determines optimal scheduling order based on multiple criteria
- Sort priority: (1) Deadline urgency (closer deadline = higher priority), (2) Priority field value, (3) Task ID (stable sort)
- Used by optimization strategies (GreedyOptimizationStrategy, BalancedOptimizationStrategy)
- Considers effective deadlines via DeadlineCalculator

**Repository Pattern** (`src/infrastructure/persistence/`)
- Abstract interface `TaskRepository` defines contract
- Concrete `JsonTaskRepository` handles JSON file persistence with atomic writes and backup
  - Atomic save: writes to temp file → creates backup → atomic rename (prevents data corruption)
  - Automatic backup: creates `.json.bak` file before each save
  - Automatic recovery: falls back to backup if main file is corrupted
  - Index optimization: maintains in-memory `_task_index` dict for O(1) lookups by ID
- Key methods: `get_all()`, `get_by_id()`, `save()`, `delete()`, `generate_next_id()`, `create()`
- Repository is responsible for ID generation and task persistence

**TimeTracker** (`src/domain/services/time_tracker.py`)
- Domain service that automatically records timestamps
- Records `actual_start` when status → IN_PROGRESS
- Records `actual_end` when status → COMPLETED/FAILED
- Invoked by use cases during status updates

**Rich Formatters** (`src/presentation/formatters/`)
- `RichTableFormatter`: Renders tasks as a table (columns: ID, Name, Priority, Status, Plan Start/End, Actual Start/End, Deadline, Duration)
- `RichGanttFormatter`: Renders timeline visualization with daily hours and status symbols
  - **Planned period**: Displays daily allocated hours as numbers (e.g., `4`, `2.5`) with background shading
  - **Actual period (IN_PROGRESS)**: Shows `◆` symbol in blue from actual_start to today
  - **Actual period (COMPLETED)**: Shows `◆` symbol in green from actual_start to actual_end
  - **Deadline**: Shows `◆` symbol in red bold
  - **No hours**: Displays ` · ` for days without allocated work
  - Weekend coloring: Saturday (blueish), Sunday (reddish), weekdays (gray)
  - Workload summary row: displays daily total hours (excluding weekends) with color-coded warnings (green ≤6h, yellow ≤8h, red >8h)
  - Uses `WorkloadCalculator` to compute daily hours from `task.daily_allocations` (if set by optimizer) or evenly distributes `estimated_duration` across planned weekdays
- Shared constants in `formatters/constants.py`: STATUS_STYLES, STATUS_COLORS_BOLD, DATETIME_FORMAT

**Custom Click Types** (`src/shared/click_types/datetime_with_default.py`)
- `DateTimeWithDefault`: Extends Click's DateTime to add default time (18:00:00) when only date provided
- Accepts: `YYYY-MM-DD` (adds 18:00:00) or `YYYY-MM-DD HH:MM:SS` (preserves time)

**Error Handlers** (`src/presentation/cli/error_handler.py`)
Two decorators for consistent error handling across CLI commands:

1. `handle_task_errors(action_name)`: For single task operations
   - Catches `TaskNotFoundException` and general `Exception`
   - Use for commands operating on a single task ID
   - Usage: `@handle_task_errors("adding task")`
   - Used in: add, update commands

2. `handle_command_errors(action_name)`: For general query operations
   - Catches only general `Exception` (lighter weight)
   - Use for commands that don't operate on specific task IDs
   - Usage: `@handle_command_errors("displaying tasks")`
   - Used in: tree, table, gantt, today commands

Not used in: start, done, rm, archive commands (these use simple for loops with inline error handling)

**Batch Operation Pattern** (used in `start`, `done`, `rm`, `archive` commands)
Commands that support multiple task IDs use simple for loops with per-task error handling:
- Accept multiple task IDs via `@click.argument("task_ids", nargs=-1, type=int, required=True)`
- Loop through task IDs with `for task_id in task_ids:`
- Handle errors per task with try/except blocks
- Add spacing between tasks when processing multiple IDs with `if len(task_ids) > 1: console.print()`
- Consistent error handling for `TaskNotFoundException` and domain-specific exceptions

### Task Model
**Task** (`src/domain/entities/task.py`)
- Core fields: id, name, priority, status, timestamp
- Time fields: planned_start/end, deadline, actual_start/end, estimated_duration
- Scheduling field: `daily_allocations` (dict mapping date strings to hours, set by ScheduleOptimizer)
- Properties:
  - `actual_duration_hours`: Auto-calculated from actual_start/end timestamps
  - `notes_path`: Returns Path to markdown notes at `$XDG_DATA_HOME/taskdog/notes/{id}.md`
  - `is_active`: True if status is PENDING or IN_PROGRESS
  - `is_finished`: True if status is COMPLETED, FAILED, or ARCHIVED
  - `can_be_modified`: True if status is not ARCHIVED
- Methods: `to_dict()`, `from_dict()` for serialization
- Datetime format: `YYYY-MM-DD HH:MM:SS`

### Notes Feature
**Task Notes** (`src/presentation/cli/commands/note.py` and `show.py`)
- Each task can have markdown notes stored at `$XDG_DATA_HOME/taskdog/notes/{task_id}.md`
- `note` command: Opens notes in editor (uses $EDITOR env var, falls back to vim/nano/vi)
- `show` command: Displays task details and renders markdown notes with Rich
  - `--raw` flag: Shows raw markdown instead of rendered
- Template auto-generated on first edit with task metadata
- Notes directory created automatically when needed

### Commands
All commands live in `src/presentation/cli/commands/` and are registered in `cli.py`:

**Task Creation & Viewing:**
- `add`: Add new task with minimal interface: `taskdog add "Task name" [--priority N]` (uses CreateTaskUseCase)
  - Detailed fields (deadline, estimate, schedule) should be set using dedicated commands after creation
- `table`: Display flat table view with sorting options (uses TaskQueryService)
  - `--sort`: Sort by id/priority/deadline/name/status/planned_start (default: id)
  - `--reverse`: Reverse sort order
  - `--all, -a`: Show all tasks including completed/archived (default: hide completed/archived)
- `today`: Show today's tasks with sorting options (uses TaskQueryService.get_today_tasks())
  - `--sort`: Sort by id/priority/deadline/name/status/planned_start (default: deadline)
  - `--reverse`: Reverse sort order
- `show`: Display task details and notes with Rich formatting (direct repository access)
  - `--raw`: Show raw markdown instead of rendered

**Task Status Management:**
- `start`: Start task(s) - supports multiple task IDs (uses StartTaskUseCase)
- `done`: Complete task(s) - supports multiple task IDs (uses CompleteTaskUseCase)

**Task Property Updates (Specialized Commands):**
- `deadline`: Set deadline with positional args: `taskdog deadline <ID> <DATE>` (uses UpdateTaskUseCase)
- `priority`: Set priority with positional args: `taskdog priority <ID> <PRIORITY>` (uses UpdateTaskUseCase)
- `rename`: Rename task with positional args: `taskdog rename <ID> <NAME>` (uses UpdateTaskUseCase)
- `estimate`: Set estimated duration with positional args: `taskdog estimate <ID> <HOURS>` (uses UpdateTaskUseCase)
- `schedule`: Set planned schedule with positional args: `taskdog schedule <ID> <START> [END]` (uses UpdateTaskUseCase)
- `update`: Multi-field update command: `taskdog update <ID> [--priority] [--status] [--planned-start] [--planned-end] [--deadline] [--estimated-duration]` (uses UpdateTaskUseCase)
  - Use for updating multiple fields at once; prefer specialized commands for single-field updates

**Task Management:**
- `rm`: Remove task(s) - supports multiple task IDs (uses RemoveTaskUseCase)
- `archive`: Archive task(s) for data retention (hidden from views) - supports multiple task IDs (uses ArchiveTaskUseCase)

**Schedule Optimization:**
- `optimize`: Auto-generate optimal task schedules based on priorities, deadlines, and workload constraints (uses OptimizeScheduleUseCase)
  - `--start-date DATE`: Start date for scheduling (default: next weekday)
  - `--max-hours-per-day FLOAT`: Maximum work hours per day (default: 6.0)
  - `--algorithm, -a NAME`: Choose optimization algorithm (default: greedy)
    - Available: greedy, balanced, backward, priority_first, earliest_deadline, round_robin, dependency_aware, genetic, monte_carlo
  - `--force, -f`: Override existing schedules for all tasks
  - `--dry-run, -d`: Preview changes without saving
  - Analyzes all tasks with `estimated_duration` set
  - Uses pluggable optimization strategies to distribute workload across weekdays
  - Shows Gantt chart, optimization summary, warnings, and configuration

**Visualization & Export:**
- `gantt`: Display Gantt chart timeline with workload summary and sorting options (uses TaskQueryService)
  - `--sort`: Sort by id/priority/deadline/name/status/planned_start (default: id)
  - `--reverse`: Reverse sort order
- `export`: Export tasks to various formats with `--format` and `--output` options (uses TaskQueryService)

**Notes:**
- `note`: Edit task notes in markdown using $EDITOR (direct repository access)

### Key Design Decisions
1. **Development installation required** - Install package in editable mode with `uv pip install -e .` for development and testing
2. **Clean Architecture layers** - Strict dependency rules: Presentation → Application → Domain ← Infrastructure
3. **Use case pattern** - Each business operation is a separate use case class with `execute()` method
4. **DTO pattern** - Input data transferred via dataclass DTOs (CreateTaskInput, StartTaskInput, etc.)
5. **CQRS-like separation** - Use cases handle writes, QueryService handles reads
6. **Repository manages ID generation** - `create()` method auto-assigns IDs, use cases are stateless
7. **Context-based DI** - Dependencies injected via `CliContext` dataclass in `ctx.obj`, accessed with `@click.pass_context`
8. **Command registration** - Commands imported and registered in `cli.py` via `cli.add_command()`
9. **Package list in pyproject.toml** - All modules must be explicitly listed in `packages` array for installation
10. **Rich for all output** - Console output uses Rich library for colors, tables, and formatting
11. **Atomic saves with backup** - JsonTaskRepository uses atomic writes (temp file + rename) and maintains `.json.bak` backup for data integrity
12. **Schedule optimization with Strategy pattern** - Multiple scheduling algorithms (9 strategies) implementing Strategy pattern, managed by StrategyFactory
13. **Unified message formatting** - All user-facing messages use `utils/console_messages.py` utilities for consistency
14. **Field-specific validation with Strategy Pattern + Registry** - TaskFieldValidatorRegistry manages field-specific validators (currently StatusValidator), using custom domain exceptions for consistent error handling; extensible design makes adding new validators simple

### Console Messaging Guidelines

All CLI commands must use the unified messaging utilities from `utils/console_messages.py` for consistent user experience.

**Message Types and Icons:**
```python
from utils.console_messages import (
    print_success,        # [green]✓[/green] Task operations
    print_error,          # [red]✗[/red] General errors
    print_validation_error,  # [red]✗[/red] Error: Validation errors
    print_warning,        # [yellow]⚠[/yellow] Warnings
    print_info,           # [cyan]ℹ[/cyan] Informational messages
)
```

**Usage Rules:**
1. **Success messages**: Use `print_success(console, action, task)` for task operations
   - Example: `print_success(console, "Added", task)`
   - Format: `✓ Added task: Task name (ID: 123)`

2. **Validation errors**: Use `print_validation_error(console, message)` for input validation
   - Example: `print_validation_error(console, "Cannot complete task that hasn't been started")`
   - Format: `✗ Error: {message}`

3. **General errors**: Use `print_error(console, action, exception)` for runtime errors
   - Example: `print_error(console, "exporting tasks", e)`
   - Format: `✗ Error {action}: {exception}`

4. **Warnings**: Use `print_warning(console, message)` for non-critical issues
   - Example: `print_warning(console, "No tasks were optimized.")`
   - Format: `⚠ {message}`

5. **Info messages**: Use `print_info(console, message)` for helpful information
   - Example: `print_info(console, "Changes not saved. Remove --dry-run to apply.")`
   - Format: `ℹ {message}`

**Constants Available:**
```python
from utils.console_messages import (
    ICON_SUCCESS, ICON_ERROR, ICON_WARNING, ICON_INFO,
    STYLE_SUCCESS, STYLE_ERROR, STYLE_WARNING, STYLE_INFO,
)
```

**When Creating New Commands:**
- Always import and use messaging utilities from `utils/console_messages.py`
- Never hardcode message icons or colors directly in command files
- Follow existing patterns in commands like `add.py`, `deadline.py`, `optimize.py`
