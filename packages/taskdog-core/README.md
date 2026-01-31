# taskdog-core

Core business logic and infrastructure for Taskdog task management system.

## Overview

This package contains the core components shared by both the Taskdog server and UI:

- **Domain Layer**: Business entities, domain services, and interfaces
- **Application Layer**: Use cases, queries, DTOs, and business logic orchestration
- **Infrastructure Layer**: Persistence implementations, external service integrations
- **Controllers**: Business logic orchestrators used by presentation layers

## Installation

```bash
pip install taskdog-core
```

For development:

```bash
pip install -e ".[dev]"
```

## Architecture

Follows Clean Architecture principles:

```text
Domain (entities, services, repositories)
  ↑
Application (use cases, queries, DTOs)
  ↑
Infrastructure (SQLite, file storage)
  ↑
Controllers (orchestration layer)
```

### Key Components

**Domain Layer** (`taskdog_core/domain/`):

- `Task` - Core entity with status, priority, deadlines, dependencies
- `TaskStatus` - PENDING, IN_PROGRESS, COMPLETED, CANCELED
- `TimeTracker` - Records actual_start/actual_end timestamps
- `TaskNotFoundException`, `TaskValidationError` - Domain exceptions

**Application Layer** (`taskdog_core/application/`):

- **Use Cases**: CreateTaskUseCase, StartTaskUseCase, OptimizeScheduleUseCase, etc.
- **Validators**: TaskFieldValidatorRegistry with Status and Dependency validators
- **Services**: WorkloadAllocator, OptimizationSummaryBuilder, TaskQueryService
- **Optimization**: 9 scheduling strategies (greedy, balanced, backward, priority_first, earliest_deadline, round_robin, dependency_aware, genetic, monte_carlo)

**Infrastructure Layer** (`taskdog_core/infrastructure/`):

- `SqliteTaskRepository` - SQLite persistence with transactional writes
- `SqliteNotesRepository` - Database-based notes storage
- `ConfigManager` - TOML configuration loading

**Controllers** (`taskdog_core/controllers/`):

- `TaskCrudController` - Create, update, delete operations
- `TaskLifecycleController` - Start, complete, pause, cancel, reopen
- `TaskRelationshipController` - Dependencies and tags
- `TaskAnalyticsController` - Statistics and optimization
- `QueryController` - Read-only operations

## Usage Example

```python
from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.infrastructure.persistence.database.sqlite_task_repository import SqliteTaskRepository
from taskdog_core.controllers.task_crud_controller import TaskCrudController
from taskdog_core.infrastructure.config.config_manager import ConfigManager
from taskdog_core.shared.utils.logger import StandardLogger

# Setup
repository = SqliteTaskRepository("sqlite:///tasks.db")
config = ConfigManager()
logger = StandardLogger("example")

# Create controller
crud_controller = TaskCrudController(repository, config, logger)

# Create a task
from taskdog_core.application.dto.task_request import CreateTaskRequest
request = CreateTaskRequest(name="My Task", priority=100)
task = crud_controller.create_task(request)
```

## Dependencies

- `holidays`: Holiday checking for scheduling
- `python-dateutil`: Date/time utilities
- `sqlalchemy`: Database ORM

## Related Packages

- [taskdog-server](../taskdog-server/): FastAPI REST API server using this package
- [taskdog-ui](../taskdog-ui/): CLI and TUI interfaces using this package
- [taskdog-client](../taskdog-client/): HTTP client library for API access

For detailed architecture documentation, see [CLAUDE.md](../../CLAUDE.md).

## Testing

```bash
pytest tests/
```

## License

MIT
