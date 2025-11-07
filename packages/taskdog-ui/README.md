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

```bash
pip install taskdog-ui
```

For development:

```bash
pip install -e ".[dev]"
```

## Usage

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
