"""Help content for TUI help screen.

This module provides content for the help screen including
basic usage, workflow guidance, and feature explanations.
"""

# Taskdog overview
TASKDOG_OVERVIEW: str = """Taskdog is a **task management system** built for individual productivity.

Manage tasks with **time tracking**, **dependencies**, **schedule optimization**,
and rich terminal visualization including Gantt charts. All data is stored
locally in SQLite for privacy and speed."""

# Basic workflow guide
BASIC_WORKFLOW: str = """## Getting Started

**1. Add a Task** - Press `a` to create a new task
  - Set priority, deadline, estimated duration
  - Add dependencies and tags if needed

**2. Start Working** - Press `s` on a task to start it
  - Status changes to **IN_PROGRESS**
  - Actual start time is recorded

**3. Complete Task** - Press `d` when done
  - Status changes to **COMPLETED**
  - Actual end time is recorded

**4. View Details** - Press `i` to see full task information
  - Shows schedule, actual tracking, and notes"""

# Main features explanation
MAIN_FEATURES: str = """## Key Features

- **Task Table** - Main view showing all your tasks
  - Use `j`/`k` or arrow keys to navigate

- **Gantt Chart** - Visual timeline of your tasks
  - Shows task schedules and workload per day
  - Use `Ctrl+J`/`Ctrl+K` to move focus between widgets

- **Search** - Press `/` to filter tasks by name
  - Smart case: case-insensitive unless query contains uppercase
  - Press `Escape` to clear search

- **Multi-Select & Batch Operations** - Operate on multiple tasks at once
  - `Space` to toggle selection, `Ctrl+A` to select all, `Ctrl+N` to clear
  - Batch start, complete, pause, cancel, archive, or delete selected tasks

- **Notes** - Press `v` to edit markdown notes for any task
  - Opens your `$EDITOR` (vim, nano, etc.)

- **Statistics** - Press `S` to view task statistics dashboard
  - Completion rates, time tracking, and trends

- **Zoom** - Press `z` to maximize/minimize the focused widget
  - Toggle between full-screen and split view for table or Gantt chart

- **Schedule Optimization** - Auto-schedule tasks based on deadlines
  - Access via `Ctrl+P` → Optimize
  - Assigns `planned_start` and `planned_end` dates
  - Respects `max_hours_per_day` limit and task dependencies

- **Fixed Tasks** - Tasks excluded from schedule optimization
  - Set `is_fixed` when creating or editing a task
  - Use for recurring meetings, standups, or time-blocked events
  - Fixed tasks keep their schedule; optimizer works around them"""

# Command palette explanation
COMMAND_PALETTE_INFO: str = """## Command Palette

Press `Ctrl+P` to open the command palette:

- **Sort** - Change task sorting order
  - Sort by deadline, priority, status, name, etc.

- **Optimize** - Run schedule optimization
  - Multiple algorithms available (greedy, balanced, etc.)

- **Export** - Export tasks to JSON, CSV, or Markdown

- **Audit** - View audit logs of task operations

**Tip**: Type to search, then press Enter to execute"""

# Quick tips for new users
QUICK_TIPS: list[str] = [
    "Use [cyan]a[/cyan] → [cyan]s[/cyan] → [cyan]d[/cyan] workflow for quick task management",
    "Edit task details with [cyan]e[/cyan], add notes with [cyan]v[/cyan]",
    "Archive with [cyan]x[/cyan] (soft delete) or permanently delete with [cyan]X[/cyan] (hard delete)",
    "Press [cyan]i[/cyan] to see full task details including notes",
    "Use [cyan]/[/cyan] for quick search, [cyan]Escape[/cyan] to clear",
    "Select multiple tasks with [cyan]Space[/cyan], then batch operate ([cyan]s[/cyan]/[cyan]d[/cyan]/[cyan]x[/cyan]/...)",
    "Check the [cyan]Keybindings[/cyan] tab for a complete list of keyboard shortcuts",
]

# Bug reports and feedback
BUG_REPORT_INFO: str = """## Bug Reports & Feature Requests

Found a bug or have a feature request? Please report it to:

**GitHub Issues**: https://github.com/Kohei-Wada/taskdog/issues"""
