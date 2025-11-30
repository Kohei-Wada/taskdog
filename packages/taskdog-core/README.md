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

## Dependencies

- `holidays`: Holiday checking for scheduling
- `python-dateutil`: Date/time utilities
- `sqlalchemy`: Database ORM

## Testing

```bash
pytest tests/
```

## License

MIT
