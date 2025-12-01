# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Taskdog is a task management system built with Python. It provides a CLI/TUI interface and a REST API server for managing tasks with time tracking, dependencies, schedule optimization, and rich terminal output. The codebase follows Clean Architecture principles and is organized as a UV workspace monorepo.

### Monorepo Structure

The repository uses UV workspace with three packages:

**taskdog-core** (`packages/taskdog-core/`): Core business logic and infrastructure

- Domain entities, use cases, repositories, validators
- SQLite persistence layer with transactional writes
- Schedule optimization algorithms (9 strategies)
- No UI dependencies - pure business logic

**taskdog-server** (`packages/taskdog-server/`): FastAPI REST API server

- Depends on: taskdog-core
- FastAPI application with automatic OpenAPI docs
- API routers: tasks, lifecycle, relationships, analytics
- Pydantic models for request/response validation
- Health check and comprehensive error handling

**taskdog-ui** (`packages/taskdog-ui/`): CLI and TUI interfaces

- Depends on: taskdog-core
- Click-based CLI commands with Rich output
- Textual-based full-screen TUI
- API client for server communication (required - CLI/TUI do not work without API server)
- Renderers for tables, Gantt charts, and markdown notes

### Data Storage & Configuration

**Tasks**: Stored in SQLite database `tasks.db` at `$XDG_DATA_HOME/taskdog/tasks.db` (fallback: `~/.local/share/taskdog/tasks.db`)

**Config**: Optional TOML at `$XDG_CONFIG_HOME/taskdog/config.toml` (fallback: `~/.config/taskdog/config.toml`)

- Sections: `[api]`, `[optimization]`, `[task]`, `[time]`, `[region]`, `[storage]`
- Settings:
  - API: cors_origins (for future Web UI)
  - Optimization: max_hours_per_day, default_algorithm
  - Task: default_priority
  - Time: default_start_hour, default_end_hour
  - Region: country (ISO 3166-1 alpha-2: "JP", "US", "GB", "DE", etc.)
  - Storage: database_url, backend
- Priority: Environment vars > CLI args > Config file > Defaults
- Server host/port: CLI arguments (`taskdog-server --host --port`)
- CLI/TUI connection: `cli.toml` or `TASKDOG_API_HOST`/`TASKDOG_API_PORT` env vars
- Access via `ctx.obj.config` (CLI) or `context.config` (TUI)

## Development Commands

```bash
# Setup (from workspace root)
make install-dev                 # Install all packages with dev dependencies (editable mode)
make install-local               # Install all packages locally for development (alias for install-core install-server install-ui)
make install                     # Install taskdog and taskdog-server as global commands via uv tool

# Per-package installation (for development)
make install-core                # Install taskdog-core only
make install-server              # Install taskdog-server (includes core)
make install-ui                  # Install taskdog-ui (includes core)

# Testing
make test                        # Run all tests (core + server + ui)
make test-core                   # Run taskdog-core tests only
make test-server                 # Run taskdog-server tests only
make test-ui                     # Run taskdog-ui tests only
make coverage                    # Run all tests with coverage report (sorted by coverage: low → high)
                                 # Used in CI - test failure will stop execution

# Single test file (run from package directory)
cd packages/taskdog-core && PYTHONPATH=src uv run python -m unittest tests/test_module.py
# Specific test method
cd packages/taskdog-core && PYTHONPATH=src uv run python -m unittest tests.test_module.TestClass.test_method

# Code Quality
make lint                        # Ruff linter on all packages
make format                      # Ruff formatter + auto-fix on all packages
make typecheck                   # mypy on all packages (progressive type checking, Phase 4)
make check                       # lint + typecheck

# Cleanup
make clean                       # Clean build artifacts and cache (stops systemd service)
make uninstall                   # Uninstall all global commands (removes systemd service)
make reinstall                   # Clean + reinstall all global commands

# Running the applications
taskdog --help                   # CLI/TUI (after make install)
taskdog-server --help            # API server (after make install)

# Development mode (without installation)
cd packages/taskdog-ui && PYTHONPATH=src uv run python -m taskdog.cli_main --help
cd packages/taskdog-server && PYTHONPATH=src uv run python -m taskdog_server.main --help

# Server examples
taskdog-server                   # Start on default 127.0.0.1:8000
taskdog-server --host 0.0.0.0 --port 3000  # Custom host/port
taskdog-server --reload          # Auto-reload for development
taskdog-server --workers 4       # Production with multiple workers
# API docs: http://localhost:8000/docs
# Health check: http://localhost:8000/health

# Systemd user service (installed automatically with make install)
systemctl --user start taskdog-server    # Start the service
systemctl --user stop taskdog-server     # Stop the service
systemctl --user status taskdog-server   # Check service status
systemctl --user restart taskdog-server  # Restart the service
journalctl --user -u taskdog-server -f   # View logs in real-time
# See contrib/README.md for detailed documentation
```

**Testing**: Uses `unittest` framework. Tests mirror package structure under `packages/*/tests/`. Use `unittest.mock` for dependencies.

## Working with the Monorepo

**Package Navigation:**

- Core business logic changes: `packages/taskdog-core/src/taskdog_core/`
- API server changes: `packages/taskdog-server/src/taskdog_server/`
- CLI/TUI changes: `packages/taskdog-ui/src/taskdog/`

**Adding Features:**

1. Add domain entities/use cases in `taskdog-core`
2. Expose via controllers (TaskController/QueryController) in `taskdog-core`
3. Add API endpoints in `taskdog-server` (if needed)
4. Add CLI commands in `taskdog-ui` (if needed)
5. Add TUI commands in `taskdog-ui` (if needed)

**Testing Workflow:**

- Test core changes: `make test-core`
- Test server changes: `make test-server`
- Test UI changes: `make test-ui`
- Test everything: `make test`

**Type Checking:**

- Mypy configured with progressive type checking (Phase 4)
- Some modules temporarily ignored (see pyproject.toml `[[tool.mypy.overrides]]`)
- Run `make typecheck` before committing

**Import Conventions:**

- Core package: `from taskdog_core.domain.entities.task import Task`
- Server package: `from taskdog_server.api.models.requests import CreateTaskRequest`
- UI package: `from taskdog.cli.commands.add import add_command`
- Cross-package: Server and UI import from `taskdog_core`

## Architecture

Clean Architecture with 5 layers across three packages: **Domain** ← **Application** → **Infrastructure** / **Presentation** / **Shared**

### Package Structure

**taskdog-core** contains Domain, Application, Infrastructure (persistence), and Shared layers:

**Domain** (`packages/taskdog-core/src/taskdog_core/domain/`): Core business logic, no external dependencies

- `entities/`: Task, TaskStatus
- `services/`: TimeTracker (records timestamps)
- `exceptions/`: TaskNotFoundException, TaskValidationError, TaskAlreadyFinishedError, TaskNotStartedError

**Application** (`packages/taskdog-core/src/taskdog_core/application/`): Business logic orchestration

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
- `dto/`: Input/Output DTOs (CreateTaskRequest, OptimizationResult, SchedulingFailure, etc.)

**Infrastructure** (`packages/taskdog-core/src/taskdog_core/infrastructure/`): External concerns

- `persistence/database/`: SqliteTaskRepository (transactional writes, indexed queries, efficient lookups)
- `persistence/file/`: FileNotesRepository (markdown note storage)
- `persistence/mappers/`: TaskDbMapper for entity-to-database mapping
- `config/`: ConfigManager (loads TOML config with fallback to defaults)

**Controllers** (`packages/taskdog-core/src/taskdog_core/controllers/`): Unified interface for task operations

- `BaseTaskController`: Abstract base class for all task controllers
- `TaskCrudController`: Orchestrates CRUD operations (create, read, update, delete)
  - Methods: create_task, update_task, delete_task, hard_delete_task
  - Instantiates use cases, constructs Request DTOs, handles config defaults
- `TaskLifecycleController`: Orchestrates lifecycle operations
  - Methods: start_task, complete_task, pause_task, cancel_task, reopen_task
  - Uses StatusChangeUseCase pattern for consistent state transitions
- `TaskRelationshipController`: Orchestrates relationship operations
  - Methods: add_dependency, remove_dependency, set_tags, log_hours
  - Handles task dependencies and tag management
- `TaskAnalyticsController`: Orchestrates analytics and optimization
  - Methods: calculate_statistics, optimize_schedule
  - Provides statistical analysis and schedule optimization
- `QueryController`: Orchestrates read operations (queries)
  - Methods: list_tasks, get_gantt_data, get_tag_statistics, get_task_by_id
  - Returns Output DTOs with metadata (TaskListOutput, GanttOutput, TagStatisticsOutput)
- All controllers used by: API server directly; CLI/TUI via HTTP API

**Shared** (`packages/taskdog-core/src/taskdog_core/shared/`): Cross-cutting utilities

- `utils/xdg_utils.py`: XDG paths (get_tasks_file, get_config_file)

**taskdog-server** contains FastAPI-specific presentation layer:

**API** (`packages/taskdog-server/src/taskdog_server/api/`):

- `app.py`: FastAPI application setup with CORS, exception handlers
- `routers/`: API route handlers
  - `tasks.py`: Task CRUD operations
  - `lifecycle.py`: Task status changes (start, complete, pause, cancel, reopen)
  - `relationships.py`: Dependencies and tags
  - `analytics.py`: Statistics and reporting
- `models/`: Pydantic request/response models
- `dependencies.py`: FastAPI dependency injection (repository, controllers)
- `context.py`: ApiContext (similar to CliContext for DI)

**taskdog-ui** contains CLI/TUI-specific presentation layer:

**CLI** (`packages/taskdog-ui/src/taskdog/cli/`):

- `cli_main.py`: Click application entry point
- `commands/`: Click command implementations (add, start, done, table, gantt, etc.)
- `context.py`: CliContext (DI container for console_writer, api_client, config, holiday_checker)
- Error handlers: `@handle_task_errors`, `@handle_command_errors` decorators

**Console** (`packages/taskdog-ui/src/taskdog/console/`):

- `ConsoleWriter` abstraction for all CLI output
- `RichConsoleWriter` implementation (Rich-based formatting)

**Renderers** (`packages/taskdog-ui/src/taskdog/renderers/`):

- `RichTableRenderer`: Task table with all fields, strikethrough for finished tasks
- `RichGanttRenderer`: Timeline with daily hours, status symbols (◆), weekend coloring, workload summary

**TUI** (`packages/taskdog-ui/src/taskdog/tui/`):

- `app.py`: Textual application main screen
- `commands/`: Command Pattern (CommandRegistry, CommandFactory, TUICommandBase)
- `screens/`, `widgets/`, `forms/`: UI components
- `services/task_service.py`: Facade wrapping TaskController + QueryController for TUI
- `styles/`: TCSS stylesheets (included via package_data)

**Infrastructure** (`packages/taskdog-ui/src/taskdog/infrastructure/`):

- `api_client.py`: HTTP client for communicating with taskdog-server (optional remote mode)

**Shared** (`packages/taskdog-ui/src/taskdog/shared/`):

- `click_types/`: Custom Click parameter types (DateTimeWithDefault adds 18:00:00 when only date provided)

### Dependency Injection

**CLI** (`taskdog-ui`): `CliContext` dataclass (console_writer, api_client, config, holiday_checker) passed via `ctx.obj`
**TUI** (`taskdog-ui`): `TUIContext` dataclass (api_client, config, holiday_checker) + CommandFactory for command instantiation
**API** (`taskdog-server`): `ApiContext` dataclass + FastAPI dependency injection via `dependencies.py`
**Communication**: CLI/TUI access all data via HTTP API client; only server directly uses repositories and controllers

### Key Components

**Task Entity** (`packages/taskdog-core/src/taskdog_core/domain/entities/task.py`)

- Fields: id, name, priority, status, planned_start/end, deadline, actual_start/end, estimated_duration, daily_allocations, is_fixed, depends_on, actual_daily_hours, tags, is_archived
- Statuses: PENDING, IN_PROGRESS, COMPLETED, CANCELED
- Always-Valid Entity: validates invariants in `__post_init__` (name non-empty, priority > 0, estimated_duration > 0 if set, tags non-empty and unique)
- Properties: actual_duration_hours, is_active, is_finished, can_be_modified, is_schedulable
- Archive Design: is_archived is a boolean flag (not a status) to preserve original task state when soft-deleted

**Repository** (`packages/taskdog-core/src/taskdog_core/infrastructure/persistence/database/sqlite_task_repository.py`)

- `SqliteTaskRepository`: Transactional writes with automatic rollback on errors
- Indexed queries for efficient lookups and filtering
- Connection pooling and proper resource management
- Used by API server only (CLI/TUI access via HTTP API, not directly)

**TimeTracker** (`packages/taskdog-core/src/taskdog_core/domain/services/time_tracker.py`):

- Records actual_start (→IN_PROGRESS), actual_end (→COMPLETED/CANCELED), clears both (→PENDING)

**Renderers** (`packages/taskdog-ui/src/taskdog/renderers/`)

- `RichTableRenderer`: Task table with all fields, strikethrough for finished tasks (uses task.is_finished)
- `RichGanttRenderer`: Timeline with daily hours, status symbols (◆), weekend coloring, workload summary, strikethrough for finished tasks
- Strikethrough applied only to COMPLETED/CANCELED tasks (task.is_finished), not archived tasks

**CLI Patterns** (`packages/taskdog-ui/src/taskdog/cli/`)

- `update_helpers.py`: Shared helper for single-field updates (deadline, priority, estimate, rename)
- `error_handler.py`: `@handle_task_errors`, `@handle_command_errors` decorators
- Batch operations: Loop + per-task error handling (start, done, pause, rm, archive)

**Controllers** (`packages/taskdog-core/src/taskdog_core/controllers/`)

- `TaskCrudController`: Orchestrates CRUD operations (create, update, delete)
- `TaskLifecycleController`: Orchestrates lifecycle operations (start, complete, pause, cancel, reopen)
- `TaskRelationshipController`: Orchestrates relationship operations (dependencies, tags, log hours)
- `TaskAnalyticsController`: Orchestrates analytics and optimization (statistics, optimize)
- `QueryController`: Orchestrates read operations (list_tasks, get_gantt_data, get_tag_statistics, get_task_by_id)
  - Returns Output DTOs with metadata (TaskListOutput, GanttOutput, TagStatisticsOutput)
- All controllers instantiate use cases, construct Request DTOs, handle config defaults
- Used by: API server directly; CLI/TUI via HTTP API client

**TUI Command Pattern** (`packages/taskdog-ui/src/taskdog/tui/commands/`)

- `@command_registry.register("name")` for automatic registration
- `TUICommandBase`: Abstract base with helpers (get_selected_task, reload_tasks, notify_*)
- `StatusChangeCommandBase`: Template Method for status changes
- `CommandFactory`: Creates commands with DI
- `TaskService`: Facade wrapping TaskController + QueryController for TUI

**API Patterns** (`packages/taskdog-server/src/taskdog_server/api/`)

- FastAPI routers: tasks, lifecycle, relationships, analytics, notes, websocket
- Pydantic models for automatic request/response validation
- Dependency injection via `dependencies.py`:
  - `CrudControllerDep` - TaskCrudController for CRUD operations
  - `LifecycleControllerDep` - TaskLifecycleController for status changes
  - `RelationshipControllerDep` - TaskRelationshipController for dependencies/tags
  - `AnalyticsControllerDep` - TaskAnalyticsController for statistics
  - `QueryControllerDep` - QueryController for read operations
  - `NotesRepositoryDep` - NotesRepository for note persistence
  - `ConnectionManagerDep` - WebSocket connection manager
- Automatic OpenAPI documentation at `/docs`
- Health check endpoint at `/health`
- WebSocket support for real-time task updates

### Data Integrity

**Entity Validation**: Task validates invariants in `__post_init__` (Always-Valid Entity pattern from DDD). Raises `TaskValidationError` for violations. No auto-correction.

**Data Integrity**: `SqliteTaskRepository` uses database constraints and transactional writes to ensure data consistency. Invalid data is rejected at write time with appropriate error messages.

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
- `report [--all] [--status] [--tag] [--start-date] [--end-date]`: Generate markdown workload report grouped by date (useful for Notion export)
- `stats [--period all|7d|30d] [--focus all|basic|time|estimation|deadline|priority|trends]`: Analytics

**Interactive**

- `note ID`: Edit markdown notes ($EDITOR)
- `tui`: Full-screen TUI (Textual) with keyboard shortcuts
  - `a`: Add task, `s`: Start, `P`: Pause, `d`: Done, `c`: Cancel, `R`: Reopen
  - `x`: Archive (soft delete), `X`: Hard delete, `i`: Details, `e`: Edit, `v`: Edit note
  - `t`: Toggle completed/canceled visibility, `r`: Refresh
  - `Ctrl+T`: Toggle sort order (ascending/descending)
  - `/`: Search, `Escape`: Clear search
  - `Ctrl+P` or `Ctrl+\`: Command palette (for optimize and other commands)
  - `q`: Quit

### Design Principles

**Core Philosophy**: Taskdog is designed for **individual task management** following GTD principles. See [DESIGN_PHILOSOPHY.md](docs/DESIGN_PHILOSOPHY.md) for detailed rationale.

**Key Design Decisions**:

- **No parent-child relationships**: Use dependencies + tags + notes instead (keeps data model simple, optimizer predictable)
- **Individual over team**: No collaboration features, no cloud sync (privacy-first, local-first)
- **Transparent algorithms**: 9 scheduling strategies you can understand (no black-box AI)

**When adding new features, ask**:

1. Does this benefit individual users? (Not teams)
2. Does this maintain simplicity? (Every feature has a cost)
3. Is this transparent? (No black boxes)
4. Does this respect privacy? (No cloud requirements)
5. Can this be achieved with existing features? (Tags, dependencies, notes)

**Implementation Principles**:

1. **Monorepo with UV Workspace**: Three packages with clear separation of concerns
   - `taskdog-core`: Pure business logic (no UI/API dependencies)
   - `taskdog-server`: FastAPI REST API (depends on core)
   - `taskdog-ui`: CLI/TUI interfaces (depends on core)
2. **Clean Architecture**: Strict layer dependencies (Presentation → Application → Domain ← Infrastructure)
3. **Specialized Controllers**: Five specialized controllers in core package (SRP - Single Responsibility Principle)
   - `TaskCrudController`, `TaskLifecycleController`, `TaskRelationshipController`, `TaskAnalyticsController`, `QueryController`
   - Used by all presentation layers (CLI, TUI, API) via HTTP API
4. **Use Case Pattern**: Each business operation = separate use case class with `execute(input_dto)`
5. **CQRS Pattern**: Commands (writes) via specialized controllers + Use Cases; Queries (reads) via QueryController + TaskQueryService
   - Write controllers: CrudController, LifecycleController, RelationshipController, AnalyticsController
   - Read controller: QueryController (list_tasks, get_gantt_data, get_tag_statistics, get_task_by_id)
   - All used by CLI, TUI, and API layers via HTTP API for consistent interface
6. **Template Method**: StatusChangeUseCase eliminates duplication across status change operations
7. **Strategy Pattern**: 9 optimization algorithms managed by StrategyFactory; field validators via TaskFieldValidatorRegistry
8. **Command Pattern (TUI)**: Auto-registration via decorator, DI via CommandFactory
9. **Always-Valid Entity**: Task validates invariants in `__post_init__` (DDD best practice)
10. **Context-based DI**: CliContext/TUIContext/ApiContext dataclasses for dependency injection
11. **ConsoleWriter Abstraction**: All CLI output through unified interface (RichConsoleWriter)
12. **Transactional Operations**: SqliteTaskRepository uses database transactions for atomic writes with automatic rollback
13. **Config Priority**: CLI args > TOML config > defaults (uses Python 3.11+ tomllib)
14. **Fixed Tasks**: is_fixed=True prevents rescheduling; hours counted in optimizer's max_hours_per_day calculation
15. **Visual Styling**: Use task.is_finished property (not direct status checks) for strikethrough; archived tasks display without strikethrough

### API Server Endpoints

The FastAPI server (`taskdog-server`) provides a REST API with automatic OpenAPI documentation at `/docs`:

**Task Management** (`/api/v1/tasks/`)

- `GET /api/v1/tasks/` - List tasks with filtering (status, tags, date ranges, archived)
- `POST /api/v1/tasks/` - Create new task
- `GET /api/v1/tasks/{task_id}` - Get task details
- `PATCH /api/v1/tasks/{task_id}` - Update task fields
- `DELETE /api/v1/tasks/{task_id}?hard=false` - Delete task (soft by default)

**Lifecycle Operations** (`/api/v1/tasks/{task_id}/`)

- `POST /api/v1/tasks/{task_id}/start` - Start task
- `POST /api/v1/tasks/{task_id}/complete` - Complete task
- `POST /api/v1/tasks/{task_id}/pause` - Pause task (reset to PENDING)
- `POST /api/v1/tasks/{task_id}/cancel` - Cancel task
- `POST /api/v1/tasks/{task_id}/reopen` - Reopen completed/canceled task
- `POST /api/v1/tasks/{task_id}/log-hours` - Log actual hours worked
- `POST /api/v1/tasks/{task_id}/archive` - Archive task (soft delete)
- `POST /api/v1/tasks/{task_id}/restore` - Restore archived task

**Relationships** (`/api/v1/tasks/{task_id}/`)

- `POST /api/v1/tasks/{task_id}/dependencies` - Add dependency
- `DELETE /api/v1/tasks/{task_id}/dependencies/{dep_id}` - Remove dependency
- `PUT /api/v1/tasks/{task_id}/tags` - Set task tags (replaces existing; tags also returned in task details)

**Notes** (`/api/v1/tasks/{task_id}/notes/`)

- `GET /api/v1/tasks/{task_id}/notes` - Get task notes (markdown)
- `PUT /api/v1/tasks/{task_id}/notes` - Update task notes
- `DELETE /api/v1/tasks/{task_id}/notes` - Delete task notes

**Analytics** (`/api/v1/`)

- `GET /api/v1/statistics` - Task statistics (period, focus filters)
- `GET /api/v1/gantt` - Gantt chart data (date ranges, filters)
- `GET /api/v1/tags/statistics` - Tag statistics

**Optimization** (`/api/v1/`)

- `POST /api/v1/optimize` - Run schedule optimization with algorithm selection
- `GET /api/v1/algorithms` - List available optimization algorithms

**Real-time Updates**:

- `WebSocket /ws` - Real-time task notifications (task_created, task_updated, task_deleted, task_status_changed)
  - Client ID-based connection management
  - Excludes event broadcaster from receiving their own events via X-Client-ID header

**System**

- `GET /health` - Health check
- `GET /` - Root redirect to docs
- `GET /docs` - OpenAPI documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)

All endpoints return JSON with proper HTTP status codes. Error responses include detailed error messages.

### Console Output (CLI/TUI)

All CLI commands use `ConsoleWriter` abstraction (`RichConsoleWriter` implementation). Access via `ctx.obj.console_writer`.

**Methods:**

- `success(action, task)`: Task operations → `✓ Added task: Task name (ID: 123)`
- `print_success(message)`: Generic success → `✓ {message}`
- `validation_error(message)`: Input validation → `✗ Error: {message}`
- `error(action, exception)`: Runtime errors → `✗ Error {action}: {exception}`
- `warning(message)`, `info(message)`, `print(message)`, `empty_line()`

Never hardcode icons/colors in commands. Follow patterns in `add.py`, `deadline.py`, `optimize.py`.
