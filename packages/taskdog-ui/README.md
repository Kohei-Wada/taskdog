# taskdog-ui

Command-line interface and terminal user interface for Taskdog task management system.

## Overview

This package provides two user interfaces for Taskdog:

### CLI (Command-Line Interface)

- 30+ commands for task management
- Rich terminal output with colors and formatting
- Batch operations support
- Export capabilities (JSON, CSV, Markdown)

### TUI (Terminal User Interface)

- Full-screen interactive interface powered by Textual
- Real-time task table with filtering and search
- Gantt chart visualization
- Vi-style keyboard navigation
- Modal dialogs for task creation and editing

## Installation

Basic installation (CLI and TUI):

```bash
pip install taskdog-ui
```

With server support (includes taskdog-server):

```bash
pip install taskdog-ui[server]
```

For development:

```bash
pip install -e ".[dev]"
```

## Prerequisites

**IMPORTANT**: The CLI and TUI require a running API server. All commands will fail without it.

### 1. Install the Server

```bash
# Server should be installed via workspace
cd /path/to/taskdog
make install
```

### 2. Start the Server

```bash
# Start the server (required before any CLI/TUI usage)
taskdog-server --host 127.0.0.1 --port 8000

# Or use systemd for auto-start (recommended)
systemctl --user start taskdog-server
systemctl --user enable taskdog-server
```

### 3. Configure API Connection

Edit `~/.config/taskdog/config.toml`:

```toml
[api]
enabled = true
host = "127.0.0.1"
port = 8000
```

Or set environment variable:

```bash
export TASKDOG_API_URL=http://127.0.0.1:8000
```

### 4. Verify Connection

```bash
# Test that CLI can connect to server
taskdog table
```

## Usage

**Note**: All commands below require the server to be running (see Prerequisites above).

### CLI Examples

```bash
# Add a task
taskdog add "Implement feature" --priority 3

# View tasks
taskdog table
taskdog gantt

# Task lifecycle
taskdog start 1
taskdog done 1

# Optimization
taskdog optimize --algorithm balanced
```

### TUI

Launch the interactive interface:

```bash
taskdog tui
```

Keyboard shortcuts:

- `a`: Add task
- `s`: Start task
- `d`: Complete task
- `e`: Edit task
- `/`: Search
- `q`: Quit

## Architecture

The UI uses:

- **Click**: CLI framework
- **Rich**: Terminal formatting and rendering
- **Textual**: TUI framework
- **httpx**: API client (for client-server mode)
- **taskdog-core**: Core business logic and infrastructure

## Dependencies

- `taskdog-core`: Core business logic
- `click`: CLI framework
- `rich`: Terminal formatting
- `textual`: TUI framework
- `httpx`: HTTP client

## Testing

```bash
pytest tests/
```

## License

MIT
