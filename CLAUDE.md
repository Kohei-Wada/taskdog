# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Taskdog is a hierarchical task management CLI tool built with Python, Click, and Rich. It supports parent-child task relationships, time tracking, and multiple task states (PENDING, IN_PROGRESS, COMPLETED, FAILED) with beautiful terminal output. The codebase follows Clean Architecture principles with clear separation between layers.

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
PYTHONPATH=src uv run python -m unittest tests/test_create_task_use_case.py

# Run a specific test case
PYTHONPATH=src uv run python -m unittest tests.test_create_task_use_case.CreateTaskUseCaseTest.test_execute_success
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
- `services/`: Domain services (TimeTracker)
- `exceptions/`: Domain-specific exceptions (TaskNotFoundException)
- No dependencies on other layers; defines core business logic

**Application Layer** (`src/application/`)
- `use_cases/`: Business logic orchestration (CreateTaskUseCase, StartTaskUseCase, etc.)
  - Each use case inherits from `UseCase[TInput, TOutput]` base class
  - Use cases are stateless and dependency-injected
- `services/`: Application services (TaskValidator - validation logic requiring repository access)
- `queries/`: Read-optimized operations (TaskQueryService with filters and sorters)
- `dto/`: Data Transfer Objects for use case inputs (CreateTaskInput, StartTaskInput, etc.)
- Depends on domain layer; defines application-specific logic

**Infrastructure Layer** (`src/infrastructure/`)
- `persistence/`: Repository implementations (TaskRepository abstract, JsonTaskRepository concrete)
- Provides concrete implementations of interfaces defined in domain/application
- Handles external concerns (file I/O, data persistence)

**Presentation Layer** (`src/presentation/`)
- `cli/commands/`: Click command implementations (add, tree, table, gantt, start, done, etc.)
- `formatters/`: Rich-based output formatting (RichTreeFormatter, RichTableFormatter, RichGanttFormatter)
- Depends on application layer use cases and queries

**Shared Layer** (`src/shared/`)
- `click_types/`: Custom Click parameter types (DateTimeWithDefault)
- Cross-cutting utilities used across layers

### Dependency Injection Pattern

Dependencies are partially managed through Click's context object (`ctx.obj`):

**Shared dependencies in `ctx.obj`** (initialized in `cli.py:36-41`):
- `repository`: JsonTaskRepository instance
- `console`: Rich Console instance

**Local instantiation in commands**:
- Use cases are created locally in each command function (e.g., `CreateTaskUseCase(repository)` in add.py:75)
- `TimeTracker` is instantiated locally in commands that need time tracking (start.py:18, done.py:18, update.py:73)
- `TaskQueryService` is instantiated locally in query commands (tree.py:24, table.py:23, today.py:36, gantt.py:41)
- Formatters are instantiated locally per command (e.g., `RichTreeFormatter()` in tree.py:34, `RichTableFormatter()` in table.py:33)

Commands access shared dependencies via `@click.pass_context` and `ctx.obj["dependency_name"]`.

### Core Components

**Use Cases** (`src/application/use_cases/`)
- Generic base class: `UseCase[TInput, TOutput]` with abstract `execute(input_dto)` method
- Concrete implementations: CreateTaskUseCase, StartTaskUseCase, CompleteTaskUseCase, UpdateTaskUseCase, RemoveTaskUseCase
- Each use case encapsulates a single business operation
- Use cases validate inputs, orchestrate domain logic, and coordinate with repository/services

**Query Service** (`src/application/queries/task_query_service.py`)
- Read-only operations optimized for data retrieval
- Methods: `get_today_tasks()`, `get_all_tasks()`, `get_incomplete_tasks_with_hierarchy()`, `get_incomplete_tasks()`
- Uses filters (TodayFilter) and sorters (TaskSorter) for query composition
- Separates reads from writes (CQRS-like pattern)

**Repository Pattern** (`src/infrastructure/persistence/`)
- Abstract interface `TaskRepository` defines contract
- Concrete `JsonTaskRepository` handles JSON file persistence
- Key methods: `get_all()`, `get_by_id()`, `get_children()`, `save()`, `delete()`, `generate_next_id()`, `create()`
- Repository is responsible for ID generation and task persistence

**TimeTracker** (`src/domain/services/time_tracker.py`)
- Domain service that automatically records timestamps
- Records `actual_start` when status → IN_PROGRESS
- Records `actual_end` when status → COMPLETED/FAILED
- Invoked by use cases during status updates

**Rich Formatters** (`src/presentation/formatters/`)
- `RichTreeFormatter`: Renders hierarchical task tree with colored status and indentation
- `RichTableFormatter`: Renders tasks as a table (columns: ID, Name, Priority, Status, Parent, Plan Start/End, Actual Start/End, Deadline, Duration)
- `RichGanttFormatter`: Renders timeline visualization with layered rendering (base → planned → actual → deadline)
  - Weekend coloring: Saturday (blueish), Sunday (reddish), weekdays (gray)
  - Status-based colors: IN_PROGRESS (blue), COMPLETED (green), FAILED (red)
- Shared constants in `formatters/constants.py`: STATUS_STYLES, STATUS_COLORS_BOLD, DATETIME_FORMAT

**Custom Click Types** (`src/shared/click_types/datetime_with_default.py`)
- `DateTimeWithDefault`: Extends Click's DateTime to add default time (18:00:00) when only date provided
- Accepts: `YYYY-MM-DD` (adds 18:00:00) or `YYYY-MM-DD HH:MM:SS` (preserves time)

**Error Handlers** (`src/presentation/cli/error_handler.py`)
Two decorators for consistent error handling across CLI commands:

1. `handle_task_errors(action_name, is_parent=False)`: For task-specific operations
   - Catches `TaskNotFoundException` and general `Exception`
   - Use for commands operating on specific task IDs
   - Usage: `@handle_task_errors("adding task", is_parent=True)`
   - Used in: add, update, remove commands

2. `handle_command_errors(action_name)`: For general query operations
   - Catches only general `Exception` (lighter weight)
   - Use for commands that don't operate on specific task IDs
   - Usage: `@handle_command_errors("displaying tasks")`
   - Used in: tree, table, gantt, today commands

Not used in: start, done commands (these handle errors per-task in loops for multiple task processing)

### Task Model
**Task** (`src/domain/entities/task.py`)
- Core fields: id, name, priority, status, parent_id, timestamp
- Time fields: planned_start/end, deadline, actual_start/end, estimated_duration
- Property: `actual_duration_hours` auto-calculated from actual_start/end timestamps
- Property: `notes_path` returns Path to markdown notes at `$XDG_DATA_HOME/taskdog/notes/{id}.md`
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
- `add`: Add new task (uses CreateTaskUseCase)
- `tree`: Display hierarchical tree view (uses TaskQueryService)
- `table`: Display flat table view (uses TaskQueryService)
- `today`: Show today's tasks (uses TaskQueryService.get_today_tasks())
- `today-new`: Alias for today command
- `start`: Start task(s) - supports multiple task IDs (uses StartTaskUseCase)
- `done`: Complete task(s) - supports multiple task IDs (uses CompleteTaskUseCase)
- `update`: Update task properties (uses UpdateTaskUseCase)
- `remove`: Remove task with cascade/orphan options (uses RemoveTaskUseCase)
- `gantt`: Display Gantt chart timeline (uses TaskQueryService)
- `note`: Edit task notes in markdown using $EDITOR (direct repository access)
- `show`: Display task details and notes with Rich formatting (direct repository access)
- `dump`: Dump all tasks as JSON (direct repository access)

### Key Design Decisions
1. **All tests require `PYTHONPATH=src`** - Source modules are not installed during test runs
2. **Clean Architecture layers** - Strict dependency rules: Presentation → Application → Domain ← Infrastructure
3. **Use case pattern** - Each business operation is a separate use case class with `execute()` method
4. **DTO pattern** - Input data transferred via dataclass DTOs (CreateTaskInput, StartTaskInput, etc.)
5. **CQRS-like separation** - Use cases handle writes, QueryService handles reads
6. **Repository manages ID generation** - `create()` method auto-assigns IDs, use cases are stateless
7. **Context-based DI** - Dependencies injected via Click's `ctx.obj` dict, accessed with `@click.pass_context`
8. **Command registration** - Commands imported and registered in `cli.py` via `cli.add_command()`
9. **Package list in pyproject.toml** - All modules must be explicitly listed in `packages` array for installation
10. **Rich for all output** - Console output uses Rich library for colors, tables, trees, and formatting
