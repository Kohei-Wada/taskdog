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
- [Design Philosophy](#design-philosophy)
- [Quick Start](#quick-start)
- [Docker](#docker)
- [Interactive TUI](#interactive-tui)
- [API Server](#api-server)
- [Commands](#commands)
- [Configuration](#configuration)
- [Workflow](#workflow)
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

## Design Philosophy

Taskdog is designed for **individual task management**, following GTD (Getting Things Done) principles:

- **Flat task structure** with dependencies (no parent-child hierarchy)
- **Focus on next actions** rather than complex project structures
- **Tags for grouping**, dependencies for ordering, notes for details
- **Transparent algorithms** - choose from 9 scheduling strategies you can understand
- **Privacy-first** - all data stored locally, no cloud requirements

**Why no subtasks?**
Individual users don't need complex hierarchies. Dependencies + tags cover 99% of personal task organization. This keeps the optimizer simple and your workflow focused.

For detailed design rationale, see [DESIGN_PHILOSOPHY.md](docs/DESIGN_PHILOSOPHY.md).

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

Run Taskdog with Docker for isolated deployment:

```bash
# Quick start with Docker Compose
cp .env.example .env   # Customize settings if needed
docker compose up -d

# Or build and run manually
docker build -t taskdog-server .
docker run -d -p 8000:8000 -v taskdog-data:/data taskdog-server
```

**Using CLI inside the container:**

```bash
docker compose exec taskdog-server taskdog table
docker compose exec taskdog-server taskdog add "New task" -p 100
```

**API access from host:** `http://localhost:8000/docs`

See [contrib/README.md](contrib/README.md) for detailed deployment options (Docker, systemd, launchd).

## Interactive TUI

Taskdog includes a full-screen terminal user interface (TUI) for managing tasks interactively.

```bash
taskdog tui
```

**Features:**

- Real-time task search and filtering
- Keyboard shortcuts for quick operations
- Sort by deadline, priority, planned start, or ID
- Visual status indicators with colors
- Task details panel with dependencies
- Command palette (`Ctrl+P`) for optimize and other commands

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

**Quick API Examples:**

```bash
# Create task
curl -X POST http://localhost:8000/api/v1/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"name": "API Task", "priority": 100}'

# List tasks
curl http://localhost:8000/api/v1/tasks/

# Start task
curl -X POST http://localhost:8000/api/v1/tasks/1/start
```

**See [API Reference](docs/API.md) for complete endpoint documentation.**

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

## Configuration

Taskdog uses separate config files for different purposes:

**Server config**: `~/.config/taskdog/server.toml`

```toml
[auth]
enabled = true

[[auth.api_keys]]
name = "my-client"
key = "your-secret-key"
```

**CLI/TUI config**: `~/.config/taskdog/cli.toml`

```toml
[api]
host = "127.0.0.1"
port = 8000
api_key = "your-secret-key"

[ui]
theme = "tokyo-night"
```

**Core config**: `~/.config/taskdog/core.toml`

```toml
[region]
country = "JP"
```

**See [Configuration Guide](docs/CONFIGURATION.md) for all available options.**

### MCP Integration (Claude Desktop)

Taskdog includes an MCP server for Claude Desktop integration. See **[taskdog-mcp README](packages/taskdog-mcp/README.md)** for setup and available tools.

Quick setup:

1. Ensure `taskdog-server` is running
2. Add to Claude Desktop config:

```json
{
  "mcpServers": {
    "taskdog": {
      "command": "taskdog-mcp"
    }
  }
}
```

## Workflow

1. **Create tasks** with priorities and estimates
2. **Set deadlines** and dependencies
3. **Run optimizer** to auto-generate schedules
4. **Track progress** with start/done commands
5. **Review** with `today` and `gantt` commands

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
