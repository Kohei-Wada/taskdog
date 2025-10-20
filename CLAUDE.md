# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Taskdog is a task management CLI tool built with Python, Click, and Rich. It supports time tracking, multiple task states (PENDING, IN_PROGRESS, COMPLETED, FAILED, ARCHIVED), and schedule optimization with beautiful terminal output. The codebase follows Clean Architecture principles with clear separation between layers.

### Data Storage

Tasks are stored in `tasks.json` following the XDG Base Directory specification:
- Default location: `$XDG_DATA_HOME/taskdog/tasks.json`
- Fallback (if `$XDG_DATA_HOME` not set): `~/.local/share/taskdog/tasks.json`
- The directory is automatically created on first run

### Configuration

Taskdog supports optional configuration via TOML file following the XDG Base Directory specification:
- Default location: `$XDG_CONFIG_HOME/taskdog/config.toml`
- Fallback (if `$XDG_CONFIG_HOME` not set): `~/.config/taskdog/config.toml`
- Configuration is optional - defaults are used if file doesn't exist

**Configuration Options:**
```toml
[optimization]
max_hours_per_day = 6.0        # Default: 6.0 - Maximum work hours per day for schedule optimization
default_algorithm = "greedy"   # Default: "greedy" - Default optimization algorithm

[task]
default_priority = 5           # Default: 5 - Default priority for new tasks

[display]
datetime_format = "%Y-%m-%d %H:%M:%S"  # Default: "%Y-%m-%d %H:%M:%S" - Datetime display format

[time]
default_start_hour = 9         # Default: 9 - Default hour for task start times (business day start)
default_end_hour = 18          # Default: 18 - Default hour for task end times and deadlines (business day end)
```

**Priority:** CLI arguments > Config file > Hardcoded defaults

Example: If config file sets `max_hours_per_day = 8.0`, the optimize command will use 8.0 by default, but `taskdog optimize --max-hours-per-day 10.0` will override it with 10.0.

**Configuration Usage:**
- All CLI commands access config via `ctx.obj.config` (from `CliContext`)
- TUI components access config via `context.config` (from `TUIContext`)
- Default priority for `add` command is now `config.task.default_priority` instead of hardcoded 100
- TUI validators accept config values as parameters (e.g., `PriorityValidator.validate(value, default_priority)`)

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

**Testing Approach:**
- Uses Python's built-in `unittest` framework
- Tests are organized in `tests/` directory mirroring the source structure
- Focus on testing use cases, repositories, domain services, and application services
- Each test file typically has one test class per component being tested
- Use `unittest.mock` for mocking dependencies (e.g., repository in use case tests)

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

**Type Checking (mypy):**
- Progressive type checking approach: Currently at Phase 3 (moderate strictness)
- Phase 3 enabled checks:
  - `check_untyped_defs = true` - Check function bodies even without type annotations
  - `strict_equality = true` - Strict type checking for equality operations
  - `warn_return_any = true` - Warn when returning Any type
  - `warn_no_return = true` - Warn about functions missing return statements
- Still disabled (reserved for Phase 4):
  - `disallow_untyped_defs` - Would require type annotations on all functions
  - `disallow_any_generics` - Would require explicit type parameters for generics
  - `disallow_untyped_calls` - Would disallow calling untyped functions
- Pre-commit hook runs mypy automatically before each commit

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
- `constants.py`: Domain-wide constants (currently only `DATETIME_FORMAT`)
  - Note: Time-related constants (DEFAULT_START_HOUR, DEFAULT_END_HOUR) were removed and migrated to `config.time`
  - DATETIME_FORMAT is kept for backward compatibility; consider using `config.display.datetime_format` for future configurability
- No dependencies on other layers; defines core business logic

**Application Layer** (`src/application/`)
- `use_cases/`: Business logic orchestration (CreateTaskUseCase, StartTaskUseCase, OptimizeScheduleUseCase, ArchiveTaskUseCase, etc.)
  - Each use case inherits from base class with `execute(input_dto)` method
  - Use cases are stateless and dependency-injected
  - `StatusChangeUseCase`: Template Method pattern base class for status change operations
    - Defines common workflow: get task → pre-process → validate → change status → post-process
    - Subclasses (StartTaskUseCase, CompleteTaskUseCase, PauseTaskUseCase, ArchiveTaskUseCase) only implement `_get_target_status()` and optional hooks
    - Eliminates code duplication across status change operations
- `validators/`: Field-specific validation logic using Strategy Pattern + Registry
  - `FieldValidator`: Abstract base class for all field validators
    - Defines uniform interface: `validate(value, task, repository)`
  - `TaskFieldValidatorRegistry` (`validator_registry.py`): Central registry managing field validators
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
  - `TaskStatusService`: Applies status changes with time tracking
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
- `dto/`: Data Transfer Objects for use case inputs and outputs
  - Input DTOs: CreateTaskInput, StartTaskInput, UpdateTaskInput, OptimizeScheduleInput, etc.
  - Output DTOs: OptimizationResult (encapsulates successful tasks, failed tasks with reasons, summary, and state changes)
  - `SchedulingFailure`: Captures individual task scheduling failures with task and reason
- Depends on domain layer; defines application-specific logic

**Infrastructure Layer** (`src/infrastructure/`)
- `persistence/`: Repository implementations (TaskRepository abstract, JsonTaskRepository concrete)
- Provides concrete implementations of interfaces defined in domain/application
- Handles external concerns (file I/O, data persistence)

**Presentation Layer** (`src/presentation/`)
- `cli/commands/`: Click command implementations (add, table, gantt, start, done, pause, optimize, archive, tui, etc.)
- `cli/context.py`: CliContext dataclass for dependency injection (console_writer, repository, time_tracker, config)
- `cli/error_handler.py`: Decorators for consistent error handling
- `console/`: ConsoleWriter abstraction for output formatting
  - `console_writer.py`: Abstract interface defining output methods (success, error, warning, info, etc.)
  - `rich_console_writer.py`: Concrete implementation using Rich library
- `renderers/`: Rich-based output formatting (RichTableRenderer, RichGanttRenderer)
- `tui/`: Text User Interface components using Textual library
  - `app.py`: Main TUI application (TaskdogTUI)
  - `context.py`: TUIContext dataclass for dependency injection (repository, time_tracker, query_service, config)
  - `commands/`: TUI command implementations using Command Pattern
    - `base.py`: TUICommandBase abstract class defining command interface
    - `registry.py`: CommandRegistry for automatic command registration
    - `factory.py`: CommandFactory for creating command instances with DI
    - Individual commands: AddTaskCommand, StartTaskCommand, CompleteTaskCommand, PauseTaskCommand, etc.
  - `screens/`: Full-screen UI screens
  - `widgets/`: Reusable TUI widgets
  - `services/task_service.py`: TaskService facade for TUI operations (uses shared Config, not TUIConfig)
- Depends on application layer use cases and queries

**Shared Layer** (`src/shared/`)
- `click_types/`: Custom Click parameter types (DateTimeWithDefault)
- `xdg_utils.py`: XDG Base Directory utilities (XDGDirectories class)
  - Handles platform-independent data file paths
  - Methods: `get_tasks_file()`, `get_note_file(task_id)`, `get_data_dir()`, `get_config_file()`
- `config_manager.py`: Configuration management (ConfigManager class)
  - Loads configuration from TOML file with fallback to defaults
  - `ConfigManager.load(config_path)`: Loads config from file or returns defaults
  - `Config` dataclass: Immutable configuration object with optimization, task, and display settings
  - Uses Python 3.11+ `tomllib` (no external dependencies)
- Cross-cutting utilities used across layers

### Dependency Injection Pattern

Dependencies are managed through Click's context object using the `CliContext` dataclass:

**CliContext** (`src/presentation/cli/context.py`):
- Dataclass containing shared dependencies: `console_writer`, `repository`, `time_tracker`, `config`
- Initialized in `cli.py` and passed to all commands via `ctx.obj`
- Commands access via `ctx.obj: CliContext` type annotation

**Local instantiation in commands**:
- Use cases are created locally in each command function (e.g., `CreateTaskUseCase(repository)`)
- `TaskQueryService` is instantiated locally in query commands
- Renderers are instantiated locally per command
- Application services (EstimatedDurationPropagator, SchedulePropagator, etc.) instantiated as needed

### Core Components

**Use Cases** (`src/application/use_cases/`)
- Generic base class: `UseCase[TInput, TOutput]` with abstract `execute(input_dto)` method
- Concrete implementations: CreateTaskUseCase, StartTaskUseCase, CompleteTaskUseCase, PauseTaskUseCase, UpdateTaskUseCase, RemoveTaskUseCase, ArchiveTaskUseCase, OptimizeScheduleUseCase
- Each use case encapsulates a single business operation
- Use cases validate inputs, orchestrate domain logic, and coordinate with repository/services

**StatusChangeUseCase** - Template Method pattern for status changes
- Base class implementing common workflow for status change operations
- Template method `execute()`: get task → pre-process → get target status → validate → apply change → post-process
- Subclasses implement `_get_target_status()` and optional hooks:
  - `_before_status_change(task)`: Pre-processing (e.g., clear time tracking on pause)
  - `_after_status_change(task)`: Post-processing (if needed)
  - `_should_validate()`: Control validation behavior
- Eliminates ~20 lines of duplication per status change use case
- Used by: StartTaskUseCase, CompleteTaskUseCase, PauseTaskUseCase, ArchiveTaskUseCase

**OptimizeScheduleUseCase** - Special use case that returns structured results
- Returns `OptimizationResult` containing:
  - `successful_tasks`: Tasks that were successfully scheduled
  - `failed_tasks`: List of `SchedulingFailure` objects (task + reason for failure)
  - `daily_allocations`: Dict mapping dates to total allocated hours
  - `summary`: OptimizationSummary with statistics
  - `task_states_before`: Backup of task states before optimization for comparison
- Handles backup of task states internally (presentation layer doesn't need to)
- Integrates OptimizationSummaryBuilder to generate summary
- Supports partial success (some tasks scheduled, others not)

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
- Clears timestamps when status → PENDING (pause operation)
- Invoked by use cases during status updates

**Rich Renderers** (`src/presentation/renderers/`)
- `RichTableRenderer`: Renders tasks as a table (columns: ID, Name, Priority, Status, Plan Start/End, Actual Start/End, Deadline, Duration)
- `RichGanttRenderer`: Renders timeline visualization with daily hours and status symbols
  - **Planned period**: Displays daily allocated hours as numbers (e.g., `4`, `2.5`) with background shading
  - **Actual period (IN_PROGRESS)**: Shows `◆` symbol in blue from actual_start to today
  - **Actual period (COMPLETED)**: Shows `◆` symbol in green from actual_start to actual_end
  - **Deadline**: Shows `◆` symbol in red bold
  - **No hours**: Displays ` · ` for days without allocated work
  - Weekend coloring: Saturday (blueish), Sunday (reddish), weekdays (gray)
  - Workload summary row: displays daily total hours (excluding weekends) with color-coded warnings (green ≤6h, yellow ≤8h, red >8h)
  - Uses `WorkloadCalculator` to compute daily hours from `task.daily_allocations` (if set by optimizer) or evenly distributes `estimated_duration` across planned weekdays
- Shared constants in `renderers/constants.py`: STATUS_STYLES, STATUS_COLORS_BOLD, DATETIME_FORMAT

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

Not used in: start, done, pause, rm, archive commands (these use simple for loops with inline error handling)

**Update Helper Pattern** (`src/presentation/cli/commands/update_helpers.py`)
Specialized single-field update commands use a shared helper to reduce code duplication:

```python
from presentation.cli.commands.update_helpers import execute_single_field_update

task = execute_single_field_update(ctx, task_id, "field_name", field_value)
ctx_obj.console_writer.update_success(task, "display name", field_value)
```

- Helper encapsulates: context extraction, use case creation, DTO building, execution
- Used by: `deadline`, `priority`, `estimate`, `rename` commands
- Reduces ~10 lines of boilerplate per command to 2 lines
- Multi-field commands like `schedule` and `update` still use inline UpdateTaskUseCase

**Batch Operation Pattern** (used in `start`, `done`, `pause`, `rm`, `archive` commands)
Commands that support multiple task IDs use simple for loops with per-task error handling:
- Accept multiple task IDs via `@click.argument("task_ids", nargs=-1, type=int, required=True)`
- Loop through task IDs with `for task_id in task_ids:`
- Handle errors per task with try/except blocks
- Add spacing between tasks when processing multiple IDs with `if len(task_ids) > 1: console_writer.empty_line()`
- Consistent error handling for `TaskNotFoundException` and domain-specific exceptions

**TUI Command Pattern** (`src/presentation/tui/commands/`)
The TUI uses a sophisticated Command Pattern with automatic registration:

**Command Components:**
1. `TUICommandBase` (`base.py`): Abstract base class for all TUI commands
   - Defines `execute()` method that subclasses implement
   - Provides helper methods: `get_selected_task()`, `reload_tasks()`, `notify_success()`, `notify_error()`, `notify_warning()`
   - Injected with app, context, and task_service dependencies

2. `CommandRegistry` (`registry.py`): Central registry for managing command classes
   - Provides `@command_registry.register("name")` decorator for automatic registration
   - Methods: `get(name)`, `has(name)`, `list_commands()`
   - Global singleton instance: `command_registry`

3. `CommandFactory` (`factory.py`): Factory for creating command instances with DI
   - Creates commands with injected dependencies (app, context, task_service)
   - Methods: `create(command_name, **kwargs)`, `execute(command_name, **kwargs)`

**Usage Pattern:**
```python
# 1. Define command with automatic registration
@command_registry.register("add_task")
class AddTaskCommand(TUICommandBase):
    def execute(self) -> None:
        # Implementation with access to self.app, self.context, self.task_service
        pass

# 2. Import command in __init__.py to trigger registration
from presentation.tui.commands.add_task_command import AddTaskCommand

# 3. Execute via factory in main app
self.command_factory.execute("add_task")
```

This pattern eliminates coupling between main app and individual commands, making it easy to add new commands without modifying app code.

### Task Model
**Task** (`src/domain/entities/task.py`)
- Core fields: id, name, priority, status, timestamp
- Time fields: planned_start/end, deadline, actual_start/end, estimated_duration
- Scheduling field: `daily_allocations` (dict mapping date strings to hours, set by ScheduleOptimizer)
- **Always-Valid Entity**: Implements invariant validation in `__post_init__` following DDD best practices
  - `name`: Must not be empty or whitespace-only (raises TaskValidationError)
  - `priority`: Must be greater than 0 (raises TaskValidationError)
  - `estimated_duration`: If provided (not None), must be greater than 0 (raises TaskValidationError)
  - Validation applies to both direct instantiation and `from_dict()` deserialization
  - No auto-correction: all invalid values are rejected with exceptions
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

### Data Integrity and Validation

**Entity Invariant Validation** (`src/domain/entities/task.py`)
- Task entity implements Always-Valid Entity pattern from DDD
- `__post_init__` validates invariants after every Task instantiation:
  - `name`: Must not be empty or whitespace-only
  - `priority`: Must be greater than 0
  - `estimated_duration`: If provided (not None), must be greater than 0
- Raises `TaskValidationError` for any violation
- No auto-correction: all invalid values are rejected immediately
- Applies to both direct instantiation and `from_dict()` deserialization

**Corrupted Data Handling** (`src/infrastructure/persistence/json_task_repository.py`)
- `_parse_tasks()` validates all tasks during JSON load
- Collects all validation errors and raises `CorruptedDataError` if any task is invalid
- `CorruptedDataError` provides:
  - List of corrupted tasks with specific error messages
  - Task ID and name for each corrupted task
  - Detailed instructions for manual correction
- CLI catches `CorruptedDataError` at startup (in `cli.py`)
- Application fails gracefully with helpful error message
- User must manually fix tasks.json to restore valid state
- Ensures data integrity: invalid data never enters the system

**Error Flow:**
1. User runs any taskdog command
2. CLI initializes JsonTaskRepository
3. Repository loads tasks.json and calls `_parse_tasks()`
4. `_parse_tasks()` attempts to create Task instances via `from_dict()`
5. If any Task violates invariants, `TaskValidationError` is caught
6. All validation errors are collected
7. `CorruptedDataError` is raised with detailed diagnostics
8. CLI catches error, displays message, and exits with code 1
9. User fixes tasks.json manually or deletes it to start fresh

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
- `pause`: Pause task(s) and reset time tracking - supports multiple task IDs (uses PauseTaskUseCase)
  - Sets status back to PENDING and clears actual_start/actual_end timestamps
  - Useful for resetting accidentally started tasks

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
  - `--max-hours-per-day FLOAT`: Maximum work hours per day (default: from config or 6.0)
  - `--algorithm, -a NAME`: Choose optimization algorithm (default: from config or greedy)
    - Available: greedy, balanced, backward, priority_first, earliest_deadline, round_robin, dependency_aware, genetic, monte_carlo
  - `--force, -f`: Override existing schedules for all tasks
  - Analyzes all tasks with `estimated_duration` set
  - Uses pluggable optimization strategies to distribute workload across weekdays
  - Shows minimal output: summary of optimized tasks, warnings for partial/full failures
  - Returns `OptimizationResult` with structured success/failure information
  - Note: Primary interface is TUI; CLI optimize command is for quick scheduling without visualization

**Visualization & Export:**
- `gantt`: Display Gantt chart timeline with workload summary and sorting options (uses TaskQueryService)
  - `--sort`: Sort by id/priority/deadline/name/status/planned_start (default: id)
  - `--reverse`: Reverse sort order
- `export`: Export tasks to various formats with `--format` and `--output` options (uses TaskQueryService)
- `stats`: Display comprehensive task statistics and analytics (uses CalculateStatisticsUseCase)
  - `--period, -p [all|7d|30d]`: Time period for filtering tasks (default: all)
  - `--focus, -f [all|basic|time|estimation|deadline|priority|trends]`: Focus on specific statistics section (default: all)
  - Shows basic counts, time tracking, estimation accuracy, deadline compliance, priority distribution, and trends

**Notes:**
- `note`: Edit task notes in markdown using $EDITOR (direct repository access)

**Interactive Interface:**
- `tui`: Launch Text User Interface for interactive task management (uses Textual library)
  - Full-screen terminal interface with keyboard shortcuts
  - Navigation: ↑/↓ arrows or j/k (vim-style)
  - Actions: a (add), s (start), p (pause), d (done), x (delete), i (details), e (edit), o (optimize), r (refresh), q (quit)

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
13. **ConsoleWriter abstraction** - All output goes through ConsoleWriter interface for consistency and testability
14. **Field-specific validation with Strategy Pattern + Registry** - TaskFieldValidatorRegistry manages field-specific validators (currently StatusValidator), using custom domain exceptions for consistent error handling; extensible design makes adding new validators simple
15. **Optional configuration with TOML** - ConfigManager loads optional TOML config with graceful fallback to defaults; uses Python 3.11+ `tomllib` (no external dependencies); priority: CLI args > config file > hardcoded defaults
16. **Unified config across CLI and TUI** - Both CLI and TUI use shared `Config` from `config_manager.py`; TUIConfig was removed to eliminate duplication; TUI validators accept config values as parameters
17. **Template Method for status changes** - StatusChangeUseCase base class eliminates duplication across start/complete/pause/archive operations using Template Method pattern
18. **TUI Command Pattern with Registry** - TUI commands use Command Pattern with automatic registration via decorator, CommandFactory for DI, and CommandRegistry for decoupled execution
19. **Always-Valid Entity Pattern** - Task entity implements invariant validation in `__post_init__` following DDD best practices; validates name (non-empty), priority (> 0), and estimated_duration (> 0 if provided); raises TaskValidationError for violations; no auto-correction to maintain data integrity
20. **Corrupted Data Detection** - JsonTaskRepository validates all tasks during load; if any task violates entity invariants, raises CorruptedDataError with detailed error messages; application startup fails gracefully prompting manual data correction; ensures data integrity at the persistence layer

### Console Output Guidelines

All CLI commands use the `ConsoleWriter` abstraction for consistent user experience.

**ConsoleWriter Interface** (`src/presentation/console/console_writer.py`):
- Abstract interface defining all output methods
- Concrete implementation: `RichConsoleWriter` (uses Rich library)

**Core Output Methods:**
```python
console_writer.success(action, task)           # ✓ Task operations (requires Task object)
console_writer.print_success(message)          # ✓ Generic success messages (no Task object)
console_writer.error(action, exception)        # ✗ General errors
console_writer.validation_error(message)       # ✗ Error: Validation errors
console_writer.warning(message)                # ⚠ Warnings
console_writer.info(message)                   # ℹ Informational messages
console_writer.print(message)                  # Raw output (for Rich objects)
console_writer.empty_line()                    # Empty line separator
```

**Usage Rules:**
1. **Success messages**: Use `success(action, task)` for task operations
   - Example: `console_writer.success("Added", task)`
   - Format: `✓ Added task: Task name (ID: 123)`

2. **Generic success messages**: Use `print_success(message)` when no Task object available
   - Example: `console_writer.print_success(f"Optimized {count} task(s) using '{algorithm}'")`
   - Format: `✓ {message}`

3. **Validation errors**: Use `validation_error(message)` for input validation
   - Example: `console_writer.validation_error("Cannot complete task that hasn't been started")`
   - Format: `✗ Error: {message}`

4. **General errors**: Use `error(action, exception)` for runtime errors
   - Example: `console_writer.error("exporting tasks", e)`
   - Format: `✗ Error {action}: {exception}`

5. **Warnings**: Use `warning(message)` for non-critical issues
   - Example: `console_writer.warning("No tasks were optimized.")`
   - Format: `⚠ {message}`

6. **Info messages**: Use `info(message)` for helpful information
   - Example: `console_writer.info("Use gantt command to view the schedule.")`
   - Format: `ℹ {message}`

**When Creating New Commands:**
- Always access `console_writer` from `CliContext`: `ctx.obj.console_writer`
- Use the appropriate ConsoleWriter method for the message type
- Never hardcode message icons or colors directly in command files
- Follow existing patterns in commands like `add.py`, `deadline.py`, `optimize.py`, `pause.py`
