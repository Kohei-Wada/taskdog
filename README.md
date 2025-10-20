# Taskdog

A personal task management CLI tool with time tracking, schedule optimization, and beautiful terminal output.

**Note**: Designed for individual use. Stores tasks locally.

## Features

- **Schedule Optimization**: 9 algorithms to auto-generate optimal schedules (respects fixed tasks & dependencies)
- **Fixed Tasks**: Mark tasks as fixed to prevent rescheduling (e.g., meetings)
- **Task Dependencies**: Define dependencies with circular detection
- **Interactive TUI**: Full-screen interface with keyboard shortcuts
- **Time Tracking**: Automatic tracking with planned vs actual comparison
- **Gantt Chart**: Visual timeline with workload analysis
- **Markdown Notes**: Editor integration with Rich rendering
- **Batch Operations**: Start/complete/pause/cancel multiple tasks at once
- **Soft Delete**: Restore removed tasks

## Installation

```bash
# Clone the repository
git clone https://github.com/Kohei-Wada/taskdog.git
cd taskdog

# Install using Make
make install
```

## Quick Start

```bash
# Add tasks with priorities and estimates
taskdog add "Design phase" -p 150
taskdog add "Implementation" -p 100
taskdog deadline 1 2025-10-20
taskdog est 1 16

# Add fixed task (won't be rescheduled)
taskdog add "Team meeting" --fixed
taskdog schedule 2 "2025-10-22 10:00" "2025-10-22 11:00"

# Add dependencies and optimize
taskdog add-dependency 2 1          # Task 2 depends on task 1
taskdog optimize                    # Auto-generate schedule

# Manage tasks
taskdog start 1                     # Start task
taskdog done 1                      # Complete task
taskdog start 2 3 4                 # Batch operations
taskdog note 1                      # Edit notes

# Visualize
taskdog table                       # Table view
taskdog gantt                       # Gantt chart
taskdog today                       # Today's tasks
taskdog tui                         # Interactive TUI
```

## Commands

### Core Commands

**Task Creation & Updates**
- `add "Task name" [-p PRIORITY] [--fixed] [-d DEP_ID]` - Create task
- `deadline ID DATE` - Set deadline (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
- `priority ID N` - Set priority (higher = more important)
- `est ID HOURS` - Set estimated duration
- `schedule ID START [END]` - Set planned schedule
- `rename ID NAME` - Rename task
- `update ID [--name] [--priority] [--status] [...]` - Multi-field update

**Task Management**
- `start ID...` - Start tasks (records actual start time)
- `done ID...` - Complete tasks (records actual end time)
- `pause ID...` - Pause tasks (reset to PENDING)
- `cancel ID...` - Cancel tasks
- `reopen ID...` - Reopen completed/canceled tasks
- `rm ID... [--hard]` - Remove tasks (soft delete by default)
- `restore ID...` - Restore soft-deleted tasks

**Dependencies**
- `add-dependency TASK_ID DEP_ID` - Add dependency (circular detection)
- `remove-dependency TASK_ID DEP_ID` - Remove dependency

**Optimization**
- `optimize [--start-date DATE] [--max-hours-per-day N] [-a ALGORITHM] [-f]`
  - Algorithms: greedy (default), balanced, backward, priority_first, earliest_deadline, round_robin, dependency_aware, genetic, monte_carlo
  - Respects fixed tasks and dependencies
  - Distributes workload across weekdays

**Visualization**
- `table [-a] [-s FIELD] [-r]` - Table view (sort by id/priority/deadline/name/status/planned_start)
- `gantt [-s FIELD] [-r]` - Gantt chart with workload analysis
- `today` - Today's tasks
- `show ID [--raw]` - Task details + notes
- `export [--format json] [-o FILE]` - Export tasks

**Notes & TUI**
- `note ID` - Edit markdown notes ($EDITOR)
- `tui` - Interactive TUI (keys: a/s/p/d/c/R/x/i/e/o/r/q)


## Task States

- **PENDING**: Not started (yellow)
- **IN_PROGRESS**: Being worked on (blue)
- **COMPLETED**: Finished (green)
- **CANCELED**: Won't be done (red)

## Data Storage

Tasks: `$XDG_DATA_HOME/taskdog/tasks.json` (fallback: `~/.local/share/taskdog/tasks.json`)

## Workflow

1. **Create tasks** with priorities and estimates
2. **Set deadlines** and dependencies
3. **Run optimizer** to auto-generate schedules
4. **Track progress** with start/done commands
5. **Review** with `today` and `gantt` commands

## Development

**Requirements**: Python 3.13+, [uv](https://github.com/astral-sh/uv)

```bash
# Install
make install

# Test
make test                           # All tests
PYTHONPATH=src uv run python -m unittest tests/test_module.py  # Single file

# Run during development
PYTHONPATH=src uv run python -m taskdog.cli --help
```

### Architecture

**Clean Architecture** with 5 layers:
- **Domain**: Entities (Task), services (TimeTracker), exceptions
- **Application**: Use cases, queries, DTOs, validators, optimization strategies
- **Infrastructure**: Repository implementations (JSON persistence)
- **Presentation**: CLI commands, renderers, TUI
- **Shared**: Cross-cutting utilities (XDG paths, config manager)

**Key Patterns**: Use Case, Repository, Dependency Injection, CQRS-like, Template Method, Strategy, Command

See [CLAUDE.md](CLAUDE.md) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.
