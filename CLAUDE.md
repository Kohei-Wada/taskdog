# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview

Taskdog is a task management CLI tool built with Python, Click, and Rich. It supports time tracking, task dependencies, multiple task states, soft deletion, and schedule optimization. The codebase follows Clean Architecture principles.

### Data Storage & Configuration

**Tasks**: Stored in `tasks.json` at `$XDG_DATA_HOME/taskdog/tasks.json` (fallback: `~/.local/share/taskdog/tasks.json`)

**Config**: Optional TOML at `$XDG_CONFIG_HOME/taskdog/config.toml` (fallback: `~/.config/taskdog/config.toml`)
- Settings: max_hours_per_day, default_algorithm, default_priority, datetime_format, default_start_hour, default_end_hour, country (for holiday checking)
- Priority: CLI args > Config file > Defaults
- Access via `ctx.obj.config` (CLI) or `context.config` (TUI)
- Country codes (ISO 3166-1 alpha-2): "JP", "US", "GB", "DE", etc.

## Development Commands

```bash
# Setup
uv pip install -e .              # Editable install (required for dev)
uv pip install -e ".[dev]"       # With dev dependencies

# Testing
make test                        # Run all tests
uv run python -m unittest tests/test_create_task_use_case.py  # Single file
uv run python -m unittest tests.test_module.TestClass.test_method  # Specific test

# Code Quality
make lint                        # Ruff linter
make format                      # Ruff formatter
make typecheck                   # mypy (Phase 3->4: 2 of 3 settings enabled, prepared for final 29 errors)
make check                       # lint + typecheck

# Installation
make install                     # Install as CLI tool
make clean                       # Clean build artifacts

# Running
taskdog --help                                          # After installation
PYTHONPATH=src uv run python -m taskdog.cli --help     # During development
```

**Testing**: Uses `unittest` framework. Tests mirror `src/` structure. Use `unittest.mock` for dependencies.

## Architecture

Clean Architecture with 5 layers: **Domain** ← **Application** → **Infrastructure** / **Presentation** / **Shared**

### Layers

**Domain** (`src/domain/`): Core business logic, no external dependencies
- `entities/`: Task, TaskStatus
- `services/`: TimeTracker (records timestamps)
- `exceptions/`: TaskNotFoundException, TaskValidationError, TaskAlreadyFinishedError, TaskNotStartedError

**Application** (`src/application/`): Business logic orchestration
- `use_cases/`: Each business operation is a separate use case with `execute(input_dto)` method
  - Base classes: `UseCase[TInput, TOutput]`, `StatusChangeUseCase` (Template Method pattern)
  - Examples: CreateTaskUseCase, StartTaskUseCase, OptimizeScheduleUseCase
- `validators/`: Field validation using Strategy Pattern + Registry
  - `TaskFieldValidatorRegistry`: Central registry for field validators
  - `StatusValidator`, `DependencyValidator` (validates dependencies are COMPLETED)
- `services/`: WorkloadAllocator, OptimizationSummaryBuilder, TaskStatusService
  - `optimization/`: 9 scheduling strategies (greedy, balanced, backward, priority_first, earliest_deadline, round_robin, dependency_aware, genetic, monte_carlo) + StrategyFactory
- `sorters/`: TaskSorter (general queries), OptimizationTaskSorter (optimization-specific)
- `queries/`: TaskQueryService, WorkloadCalculator (computes daily hours for read-only operations, CQRS-like)
- `dto/`: Input/Output DTOs (CreateTaskInput, OptimizationResult, SchedulingFailure, etc.)

**Infrastructure** (`src/infrastructure/`): External concerns
- `persistence/`: JsonTaskRepository (atomic writes, backups, O(1) lookups via index)

**Presentation** (`src/presentation/`): User interfaces
- `cli/`: Click commands, CliContext (DI container), error handlers
- `console/`: ConsoleWriter abstraction (RichConsoleWriter implementation)
- `renderers/`: RichTableRenderer, RichGanttRenderer
- `tui/`: Textual-based TUI with Command Pattern (CommandRegistry, CommandFactory, TUICommandBase)
- `controllers/`: TaskController (writes), QueryController (reads) - orchestrate use cases/queries for all presentation layers

**Shared** (`src/shared/`): Cross-cutting utilities
- `xdg_utils.py`: XDG paths (get_tasks_file, get_config_file)
- `config_manager.py`: ConfigManager (loads TOML config with fallback to defaults)
- `click_types/`: DateTimeWithDefault (adds 18:00:00 when only date provided)

### Dependency Injection

**CLI**: `CliContext` dataclass (console_writer, repository, time_tracker, config) passed via `ctx.obj`
**TUI**: `TUIContext` dataclass + CommandFactory for command instantiation
**Local**: Use cases, renderers, and query services instantiated per command

### Key Components

**Task Entity** (`src/domain/entities/task.py`)
- Fields: id, name, priority, status, planned_start/end, deadline, actual_start/end, estimated_duration, daily_allocations, is_fixed, depends_on, actual_daily_hours, tags, is_archived
- Statuses: PENDING, IN_PROGRESS, COMPLETED, CANCELED
- Always-Valid Entity: validates invariants in `__post_init__` (name non-empty, priority > 0, estimated_duration > 0 if set, tags non-empty and unique)
- Properties: actual_duration_hours, is_active, is_finished, can_be_modified, is_schedulable
- Archive Design: is_archived is a boolean flag (not a status) to preserve original task state when soft-deleted

**Repository** (`JsonTaskRepository`)
- Atomic saves: temp file → backup → atomic rename
- O(1) lookups via in-memory index
- Auto-recovery from backup on corruption

**TimeTracker**: Records actual_start (→IN_PROGRESS), actual_end (→COMPLETED/CANCELED), clears both (→PENDING)

**Renderers**
- `RichTableRenderer`: Task table with all fields, strikethrough for finished tasks (uses task.is_finished)
- `RichGanttRenderer`: Timeline with daily hours, status symbols (◆), weekend coloring, workload summary, strikethrough for finished tasks
- Strikethrough applied only to COMPLETED/CANCELED tasks (task.is_finished), not archived tasks

**CLI Patterns**
- `update_helpers.py`: Shared helper for single-field updates (deadline, priority, estimate, rename)
- `error_handler.py`: `@handle_task_errors`, `@handle_command_errors` decorators
- Batch operations: Loop + per-task error handling (start, done, pause, rm, archive)

**Controllers** (`src/presentation/controllers/`)
- `TaskController`: Orchestrates write operations (commands)
  - Methods: start_task, complete_task, create_task, update_task, archive_task, etc.
  - Instantiates use cases, constructs Input DTOs, handles config defaults
  - Used by: CLI commands, TUI TaskService, future API handlers
- `QueryController`: Orchestrates read operations (queries)
  - Methods: list_tasks, get_gantt_data, get_tag_statistics, get_task_by_id
  - Returns Output DTOs with metadata (TaskListOutput, GanttOutput, TagStatisticsOutput)
  - Used by: CLI commands (table, gantt, tags, export, report), TUI TaskService, future API endpoints

**TUI Command Pattern**
- `@command_registry.register("name")` for automatic registration
- `TUICommandBase`: Abstract base with helpers (get_selected_task, reload_tasks, notify_*)
- `StatusChangeCommandBase`: Template Method for status changes
- `CommandFactory`: Creates commands with DI
- `TaskService`: Facade wrapping TaskController + QueryController for TUI

### Data Integrity

**Entity Validation**: Task validates invariants in `__post_init__` (Always-Valid Entity pattern from DDD). Raises `TaskValidationError` for violations. No auto-correction.

**Corrupted Data Handling**: `JsonTaskRepository._parse_tasks()` validates all tasks on load. Raises `CorruptedDataError` with diagnostics if any task is invalid. CLI catches at startup and exits gracefully.

### CLI Commands

Commands in `src/presentation/cli/commands/`, registered in `cli.py`:

**Creation & Viewing**
- `add "Task name" [--priority N] [--fixed] [--depends-on ID] [--tag TAG]`: Create task (multiple -d/-t allowed)
- `table [--sort FIELD] [--reverse] [--all] [--fields LIST] [--status STATUS] [--tag TAG] [--start-date] [--end-date]`: Table view with filtering
- `today [--sort FIELD] [--reverse]`: Today's tasks (deadline today, planned includes today, or IN_PROGRESS)
- `week [--sort FIELD] [--reverse]`: This week's tasks
- `show ID [--raw]`: Task details + notes (markdown rendered or raw)

**Status Management** (support multiple IDs)
- `start ID...`: Start tasks
- `done ID...`: Complete tasks
- `pause ID...`: Reset to PENDING, clear timestamps
- `cancel ID...`: Mark as CANCELED
- `reopen ID...`: Reset to PENDING (no dependency validation)

**Updates** (single-field commands use `update_helpers.py`)
- `deadline ID DATE`, `priority ID N`, `rename ID NAME`, `estimate ID HOURS`, `schedule ID START [END]`
- `update ID [--priority] [--status] [...]`: Multi-field update

**Management**
- `rm ID... [--hard]`: Soft delete (default, sets is_archived=true) or hard delete (permanent removal)
- `restore ID...`: Restore soft-deleted tasks (sets is_archived=false)
- `add-dependency TASK_ID DEPENDS_ON_ID`: Add dependency (DFS cycle detection)
- `remove-dependency TASK_ID DEPENDS_ON_ID`: Remove dependency
- `tags [ID] [TAG...]`: List all tags, show task tags, or set task tags

**Time & Optimization**
- `log-hours ID HOURS [--date DATE]`: Log actual hours
- `optimize [--start-date] [--max-hours-per-day] [--algorithm] [--force]`: Auto-schedule (9 strategies available)

**Visualization**
- `gantt [--sort] [--reverse] [--all] [--status] [--tag] [--start-date] [--end-date]`: Gantt chart with workload summary (default sort: deadline, shows non-archived tasks by default)
- `table [--sort] [--reverse] [--all] [--fields] [--status] [--tag] [--start-date] [--end-date]`: Task table with filtering (shows non-archived tasks by default)
- `today`: Today's tasks (deadline today, planned includes today, or IN_PROGRESS)
- `week`: This week's tasks
- `export [--format json|csv] [--output] [--fields] [--all] [--status] [--tag]`: Export tasks (exports non-archived tasks by default)
- `stats [--period all|7d|30d] [--focus all|basic|time|estimation|deadline|priority|trends]`: Analytics

**Interactive**
- `note ID`: Edit markdown notes ($EDITOR)
- `tui`: Full-screen TUI (Textual) with keyboard shortcuts
  - `a`: Add task, `s`: Start, `P`: Pause, `d`: Done, `c`: Cancel, `R`: Reopen
  - `x`: Archive (soft delete), `X`: Hard delete, `i`: Details, `e`: Edit, `v`: Edit note
  - `t`: Toggle completed/canceled visibility, `o`: Optimize, `r`: Refresh
  - `S`: Sort dialog (deadline/planned_start/priority/estimated_duration/id)
  - `/`: Search, `Escape`: Clear search, `q`: Quit

### Design Principles

1. **Clean Architecture**: Strict layer dependencies (Presentation → Application → Domain ← Infrastructure)
2. **Use Case Pattern**: Each business operation = separate use case class with `execute(input_dto)`
3. **CQRS Pattern**: Commands (writes) via TaskController + Use Cases; Queries (reads) via QueryController + TaskQueryService
   - TaskController: Orchestrates write use cases (start, complete, create, update, archive, etc.)
   - QueryController: Orchestrates read queries (list_tasks, get_gantt_data, get_tag_statistics, get_task_by_id)
   - Both used by CLI, TUI, and future API layers for consistent interface
4. **Template Method**: StatusChangeUseCase eliminates duplication across status change operations
5. **Strategy Pattern**: 9 optimization algorithms managed by StrategyFactory; field validators via TaskFieldValidatorRegistry
6. **Command Pattern (TUI)**: Auto-registration via decorator, DI via CommandFactory
7. **Always-Valid Entity**: Task validates invariants in `__post_init__` (DDD best practice)
8. **Context-based DI**: CliContext/TUIContext dataclasses for dependency injection
9. **ConsoleWriter Abstraction**: All CLI output through unified interface (RichConsoleWriter)
10. **Atomic Operations**: JsonTaskRepository uses temp file → backup → atomic rename
11. **Config Priority**: CLI args > TOML config > defaults (uses Python 3.11+ tomllib)
12. **Fixed Tasks**: is_fixed=True prevents rescheduling; hours counted in optimizer's max_hours_per_day calculation
13. **Visual Styling**: Use task.is_finished property (not direct status checks) for strikethrough; archived tasks display without strikethrough

### Console Output

All CLI commands use `ConsoleWriter` abstraction (`RichConsoleWriter` implementation). Access via `ctx.obj.console_writer`.

**Methods:**
- `success(action, task)`: Task operations → `✓ Added task: Task name (ID: 123)`
- `print_success(message)`: Generic success → `✓ {message}`
- `validation_error(message)`: Input validation → `✗ Error: {message}`
- `error(action, exception)`: Runtime errors → `✗ Error {action}: {exception}`
- `warning(message)`, `info(message)`, `print(message)`, `empty_line()`

Never hardcode icons/colors in commands. Follow patterns in `add.py`, `deadline.py`, `optimize.py`.
