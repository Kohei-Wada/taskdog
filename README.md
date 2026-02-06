# Taskdog

[![CI](https://github.com/Kohei-Wada/taskdog/actions/workflows/ci.yml/badge.svg)](https://github.com/Kohei-Wada/taskdog/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![Code style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

A task management system with CLI/TUI interfaces and REST API server, featuring time tracking, schedule optimization, and beautiful terminal output.

**Note**: Designed for individual use. Stores tasks locally in SQLite database.

https://github.com/user-attachments/assets/47022478-078d-4ad9-ba7d-d1cd4016e105

**Architecture**: UV workspace monorepo with five packages:

- **taskdog-core**: Core business logic and SQLite persistence
- **taskdog-client**: HTTP API client library
- **taskdog-server**: FastAPI REST API server
- **taskdog-ui**: CLI and TUI interfaces
- **taskdog-mcp**: MCP server for Claude Desktop integration

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Docker](#docker)
- [Commands](#commands)
- [Development](#development)
- [Contributing](#contributing)

## Documentation

- **[Quick Start Guide](docs/QUICKSTART.md)** - Step-by-step setup in 5 minutes
- **[CLI Commands Reference](docs/COMMANDS.md)** - Complete command documentation
- **[API Reference](docs/API.md)** - REST API endpoints and examples
- **[Configuration Guide](docs/CONFIGURATION.md)** - All configuration options
- **[Development Guide](CLAUDE.md)** - Architecture and development workflow
- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute
- **[Design Philosophy](docs/DESIGN_PHILOSOPHY.md)** - Why Taskdog works this way

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
- **Audit Logging**: Track all task operations with client identification
- **MCP Integration**: Native Claude Desktop support via Model Context Protocol

## Quick Start

**Requirements**: Python 3.11+, [uv](https://github.com/astral-sh/uv)

**Supported Platforms**: Linux, macOS (Windows support coming soon)

```bash
git clone https://github.com/Kohei-Wada/taskdog.git
cd taskdog
make install
```

For complete setup including API key configuration and server startup, see **[Quick Start Guide](docs/QUICKSTART.md)**.

### After Setup

```bash
taskdog add "My first task" --priority 10
taskdog table
taskdog tui
```

## Docker

```bash
cp .env.example .env   # Customize settings if needed
docker compose up -d
```

See [contrib/README.md](contrib/README.md) for detailed deployment options (Docker, systemd, launchd).

## Commands

**Common Commands:**

```bash
# Task management
taskdog add "Task name" -p 150           # Create task with priority
taskdog start 1                          # Start task
taskdog done 1                           # Complete task
taskdog rm 1                             # Archive task (soft delete)

# Dependencies & Tags
taskdog add-dependency 2 1               # Task 2 depends on task 1
taskdog tags 1 backend api               # Set tags

# Visualization
taskdog table                            # Table view
taskdog gantt                            # Gantt chart
taskdog today                            # Today's tasks
taskdog tui                              # Interactive TUI

# Optimization
taskdog optimize                         # Auto-schedule tasks
taskdog optimize -a balanced             # Use balanced algorithm

# Auditing
taskdog audit-logs                       # View operation history
```

**See [CLI Commands Reference](docs/COMMANDS.md) for complete command documentation.**

## Development

**Requirements**: Python 3.11+, [uv](https://github.com/astral-sh/uv)

**Quick start:**

```bash
# Setup
make install-dev                    # Install with dev dependencies

# Testing
make test                           # Run all tests with coverage

# Code Quality
make lint                           # Lint code
make format                         # Format code
make check                          # Lint + typecheck
```

**Architecture**: UV workspace monorepo with Clean Architecture principles.

- **taskdog-core**: Domain, Application, Infrastructure layers
- **taskdog-client**: HTTP API client library
- **taskdog-server**: FastAPI REST API (Presentation layer)
- **taskdog-ui**: CLI/TUI interfaces (Presentation layer)
- **taskdog-mcp**: MCP server for AI integration (Presentation layer)

**See [CLAUDE.md](CLAUDE.md) for detailed development guide and architecture documentation.**

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on:

- Development setup and workflow
- Coding standards and testing
- Commit guidelines and PR process
- Project structure and architecture

**CI/CD**: All pull requests automatically run:

- Linting (`make lint`)
- Type checking (`make typecheck`)
- Tests with coverage (`make test`)

Coverage reports are displayed in CI logs, sorted by coverage (low → high) to highlight areas needing improvement.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
