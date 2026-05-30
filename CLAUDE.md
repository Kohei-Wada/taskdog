# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Taskdog is a Python task management system with a CLI/TUI and a REST API server. It manages tasks with time tracking, dependencies, schedule optimization, and rich terminal output. The codebase follows Clean Architecture and is organized as a UV workspace monorepo.

## Monorepo Structure

Five packages under `packages/`:

- **taskdog-core**: Pure business logic. Domain entities, use cases, controllers, validators, optimization strategies, SQLite + SQLAlchemy persistence with Alembic migrations. No UI/API dependencies.
- **taskdog-server**: FastAPI REST API (depends on core). Routers, Pydantic request/response models, OpenAPI docs at `/docs`, health check, app-level exception handlers.
- **taskdog-client**: HTTP client (`TaskdogClient`) for the server (depends on core). Used by CLI/TUI/MCP.
- **taskdog-ui**: CLI (Click + Rich) and TUI (Textual), depends on core + client.
- **taskdog-mcp**: MCP server for Claude Desktop (depends on client).

**Communication**: CLI/TUI/MCP reach all data through the HTTP API client. Only the server uses repositories and controllers directly.

## Data Storage & Configuration

- **Tasks**: SQLite at `$XDG_DATA_HOME/taskdog/tasks.db` (fallback `~/.local/share/taskdog/tasks.db`).
- **Config**: optional TOML at `$XDG_CONFIG_HOME/taskdog/` (fallback `~/.config/taskdog/`):
  - `core.toml` — `[time]`, `[region]`, `[storage]` (default_start/end_time, country, database_url, backend)
  - `server.toml` — `[auth]` (enabled, api_keys)
  - `cli.toml` — `[api]`, `[ui]`, `[notes]`, `[keybindings]` (host, port, api_key, theme)
  - `mcp.toml` — `[api]` (host, port, api_key)
- **Priority**: Environment vars > CLI args > Config file > Defaults.
- Server host/port via `taskdog-server --host --port`. CLI/TUI connection via `cli.toml` or `TASKDOG_API_HOST` / `TASKDOG_API_PORT`. Access config via `ctx.obj.config` (CLI) or `context.config` (TUI).

## Development Commands

```bash
make install-dev      # install all packages with dev deps (editable)
make test             # all tests with coverage; also test-core / test-server / test-ui
make lint             # ruff check
make format           # ruff format + autofix
make typecheck        # mypy (strict on production code; tests.* relaxed)
make check            # lint + typecheck

# Single test (run from the package dir)
cd packages/taskdog-core && PYTHONPATH=src uv run python -m pytest tests/test_module.py::TestClass::test_method -v

# Run without installing
cd packages/taskdog-ui && PYTHONPATH=src uv run python -m taskdog.cli_main --help
cd packages/taskdog-server && PYTHONPATH=src uv run python -m taskdog_server.main --help
```

Tests use `pytest`, mirror package structure under `packages/*/tests/`, and mock dependencies with `unittest.mock`. Run `make check` before committing. For the systemd user service and global install, see `contrib/README.md` and the `Makefile`.

## Architecture

Clean Architecture, dependencies point inward: **Presentation → Application → Domain ← Infrastructure**. The domain layer stays framework-free.

### taskdog-core layers (`packages/taskdog-core/src/taskdog_core/`)

- **`domain/`**: `entities/` (Task, TaskStatus), `services/` (ITimeProvider, IHolidayChecker interfaces), `exceptions/`, `constants.py`. No external dependencies — pure dataclass entities.
- **`application/`**: `use_cases/` (one per operation, `execute(input_dto)`; base `UseCase[TInput, TOutput]`, `StatusChangeUseCase`), `validators/` (Strategy + `TaskFieldValidatorRegistry`), `services/` (incl. `optimization/` — 9 strategies + `StrategyFactory`), `sorters/`, `queries/` (`TaskQueryService`, `queries/workload/`, `queries/filters/`), `dto/` (Pydantic `BaseModel` input/output DTOs).
- **`infrastructure/`**: `persistence/database/` (`SqliteTaskRepository`, `SqliteNotesRepository` — SQLAlchemy ORM, transactional sessionmaker, indexed queries), `persistence/mappers/` (`TaskDbMapper`), `config/` (`ConfigManager`).
- **`controllers/`**: unified operation interface used by the server directly (and by CLI/TUI via HTTP). See below.
- **`shared/`**: `utils/xdg_utils.py`.

### Controllers (`controllers/`)

`BaseTaskController` is the abstract base. Specialized controllers (SRP):

- `TaskCrudController` — create_task, update_task, delete_task, hard_delete_task
- `TaskLifecycleController` — start/complete/pause/cancel/reopen (via `StatusChangeUseCase`)
- `TaskRelationshipController` — add_dependency, remove_dependency, set_task_tags, delete_tag
- `TaskAnalyticsController` — calculate_statistics, optimize_schedule
- `BulkTaskController` — batch lifecycle/CRUD operations
- `NotesController` — task notes
- `QueryController` — list_tasks, get_gantt_data, get_tag_statistics, get_task_by_id (returns Output DTOs with metadata)
- `AuditLogController` — save, log_operation, get_logs, get_by_id, count_logs

Controllers instantiate use cases, build request DTOs, and apply config defaults.

### taskdog-server (`packages/taskdog-server/src/taskdog_server/api/`)

- `app.py`: FastAPI setup + app-level exception handlers (domain exceptions → HTTP responses).
- `routers/`: tasks, lifecycle, relationships, analytics, notes, audit, bulk, tags, websocket.
- `models/`: Pydantic request/response models (responses built via `model_validate(dto, from_attributes=True)`).
- `dependencies.py`: FastAPI DI (`CrudControllerDep`, `LifecycleControllerDep`, … `NotesRepositoryDep`, `ConnectionManagerDep`).
- Endpoints documented at `/docs` (OpenAPI) and `/redoc`; health at `/health`; real-time updates over `WebSocket /ws` (client-ID via `token` query param).

### taskdog-ui (`packages/taskdog-ui/src/taskdog/`)

- **CLI** (`cli/`): `cli_main.py` (Click entry point), `commands/` (one file per command, registered in `cli_main.py`), `context.py` (`CliContext`), `error_handler.py` (`@handle_task_errors`, `@handle_command_errors`). Batch commands loop over IDs with per-task error handling.
- **TUI** (`tui/`): `app.py` (Textual main screen), `commands/` (Command Pattern: `@command_registry.register`, `TUICommandBase`, `StatusChangeCommandBase`, `CommandFactory`), `screens/`, `widgets/`, `forms/`, `state/` (`TUIState`), `services/` (`WebSocketHandler`, `EventHandlerRegistry`, `TaskUIManager`), `styles/` (TCSS).
- **Console** (`console/`): `ConsoleWriter` abstraction, `RichConsoleWriter` implementation — all CLI output goes through it.
- **Presentation** (`presenters/`, `view_models/`, `renderers/`): presenters convert DTOs → ViewModels; renderers (`RichTableRenderer`, `RichGanttRenderer`) format ViewModels for display. ViewModels are frozen data carriers; formatting happens in renderers.
- Also: `exporters/`, `formatters/`, `utils/`, `services/`, `shared/click_types/` (`DateTimeWithDefault` appends 18:00:00 when only a date is given).

### Dependency Injection

`CliContext` (console_writer, api_client, config) via `ctx.obj`; `TUIContext` (api_client, state, config) + `CommandFactory`; `ApiContext` + FastAPI DI.

### Key Components & Non-obvious Rules

- **Task entity** (`domain/entities/task.py`): Always-Valid Entity — validates invariants in `__post_init__` (name non-empty, priority > 0, estimated_duration > 0 if set, tags non-empty & unique), raising `TaskValidationError`. No auto-correction. Statuses: PENDING, IN_PROGRESS, COMPLETED, CANCELED. Properties: actual_duration_hours, is_active, is_finished, can_be_modified, is_schedulable.
- **Archive**: `is_archived` is a boolean flag, not a status, so the original status is preserved on soft delete.
- **Fixed tasks**: `is_fixed=True` blocks rescheduling but its hours still count toward the optimizer's max_hours_per_day.
- **Strikethrough**: apply only to finished tasks (`task.is_finished` — COMPLETED/CANCELED), never to archived tasks.
- **Repository**: `SqliteTaskRepository` uses transactional SQLAlchemy sessions with automatic rollback; used by the server only.
- **DTOs**: `application/dto/` are Pydantic `BaseModel`s; the client deserializes API responses via `model_validate`. Domain entities remain dataclasses.

## Conventions

- **Imports**: `from taskdog_core.domain.entities.task import Task`; `from taskdog_server.api.models.requests import CreateTaskRequest`; `from taskdog.cli.commands.add import add_command`. Server and UI import from `taskdog_core`.
- **Console output**: never hardcode icons/colors — use `ConsoleWriter` (`ctx.obj.console_writer`): `success(action, task)`, `print_success(msg)`, `validation_error(msg)`, `error(action, exc)`, `warning/info/print/empty_line`. Follow patterns in `cli/commands/add.py`, `optimize.py`.
- **Type checking**: mypy strict on production code; only `tests.*` is relaxed.

## CLI & API surface

- **CLI commands**: see `taskdog --help`. Implementations in `cli/commands/`, registered in `cli_main.py`. Status/management commands accept multiple IDs. `tui` launches the full-screen Textual app (keybindings shown in-app and configurable via `cli.toml [keybindings]`).
- **API endpoints**: see `/docs` (OpenAPI). Versioned under `/api/v1/`, grouped by the routers listed above.

## Design Philosophy

Taskdog is for **individual** task management following GTD. See [DESIGN_PHILOSOPHY.md](docs/DESIGN_PHILOSOPHY.md).

Key decisions:

- **No parent-child relationships** — use dependencies + tags + notes (keeps the model simple and the optimizer predictable).
- **Individual over team** — no collaboration, no cloud sync (privacy-first, local-first).
- **Transparent algorithms** — 9 understandable scheduling strategies, no black-box AI.

When adding a feature, ask: does it benefit individual users? does it keep things simple? is it transparent? does it respect privacy? can it be done with existing features (tags, dependencies, notes)?
