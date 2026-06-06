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

### Navigate

Move around the task table and Gantt chart.

- `j`/`k` or arrow keys to move the cursor
- `g`/`G` to jump to top/bottom
- `Ctrl+J`/`Ctrl+K` to move focus between the table and Gantt
- `z` to zoom (maximize) the focused widget

### Manage tasks

Create, inspect, edit, and move tasks through their lifecycle.

- `a` add, `e` edit, `i` view full details, `r` refresh from the server
- Lifecycle: `s` start, `d` done, `c` cancel, `P` pause, `R` reopen
- `x` archive (soft delete, keeps the original status), `X` delete permanently

### Track time

- `f` fix the actual start/end times or duration of a task — correct or clear
  time-tracking data after the fact

### Select & act in bulk

Operate on many tasks at once.

- `Space` to select the current task, `Ctrl+A` select all, `Ctrl+N` clear
- Lifecycle keys (`s` start, `d` done, `c` cancel, `P` pause, `x` archive)
  apply to every selected task; with no selection they act on the cursor
- Optimize uses the selection too — only selected tasks are scheduled
  (all tasks if nothing is selected)

### Search & filter

Press `/` (or `Ctrl+R`) to filter, `Escape` to clear.

- Substring match with smart case (case-insensitive unless query has uppercase)
- fzf-style exclusion: `!term` excludes matches
- Status filters: `!completed`, `!pending`, `!in_progress`, `!canceled`,
  or `!status:VALUE`
- Tag filter: `!tag:NAME`
- Multiple tokens combine with AND (e.g. `bug !completed`)

### Gantt chart

Visual timeline with workload per day.

- `w`/`b` jump one week forward/back, `T` jump to today
- `Enter` jumps the window to the selected task's actual period
- `H`/`L` pan into the past/future, `0`/`$` go to row start/end
- Lifecycle keys work on the task under the Gantt cursor too
- `t` toggles the search filter for the Gantt view

### Notes

- `v` edits markdown notes for any task, opening your `$EDITOR` (vim, nano, etc.)

### Schedule optimization

Auto-schedule tasks based on deadlines via `Ctrl+P` → Optimize.

- Choose an algorithm (greedy, balanced, and more) and set
  `max_hours_per_day`, start date, and whether to schedule on all days
- Assigns `planned_start` and `planned_end`, respecting dependencies
- **Fixed tasks** (`is_fixed`) keep their schedule; the optimizer works
  around them — use for meetings, standups, or time-blocked events

### Statistics

- `S` opens the statistics dashboard — completion rates, workload, and
  progress metrics

### Export & backup

- `Ctrl+P` → Export writes all tasks to `~/Downloads` as JSON, CSV, or Markdown
- `Ctrl+P` → Backup downloads a consistent `.db` snapshot to `~/Downloads`

### Audit log

- `Ctrl+P` → Audit Logs shows the history of operations (what changed, when,
  and from which client)

### Archived tasks

- `x` archives a task without losing its status; `Ctrl+P` → Toggle Archive
  shows or hides archived tasks in the list"""

# Command palette explanation
COMMAND_PALETTE_INFO: str = """## Command Palette

Press `Ctrl+P` to open the command palette:

- **Sort** - Change task sorting order
  - Sort by deadline, priority, status, name, etc.

- **Optimize** - Run schedule optimization
  - Multiple algorithms available (greedy, balanced, etc.)
  - Optimizes only selected tasks, or all tasks if none are selected

- **Export** - Export tasks to JSON, CSV, or Markdown (saved to `~/Downloads`)

- **Backup** - Download a `.db` snapshot of the database to `~/Downloads`

- **Audit Logs** - Open the operation history screen

- **Toggle Archive** - Show or hide archived tasks in the list

- **Keys** - View all keyboard shortcuts
  - Complete list of keybindings with descriptions

**Tip**: Type to search, then press Enter to execute"""

# Quick tips for new users
QUICK_TIPS: list[str] = [
    "Press [cyan]Ctrl+P[/cyan] then type [cyan]'Keys'[/cyan] to see all keyboard shortcuts",
    "Use [cyan]a[/cyan] → [cyan]s[/cyan] → [cyan]d[/cyan] workflow for quick task management",
    "Edit task details with [cyan]e[/cyan], add notes with [cyan]v[/cyan]",
    "Archive tasks with [cyan]x[/cyan]; toggle [cyan]Ctrl+P[/cyan] → [cyan]Toggle Archive[/cyan] to see them",
    "Press [cyan]i[/cyan] to see full task details including notes",
    "Use [cyan]/[/cyan] for quick search, [cyan]Escape[/cyan] to clear",
    "Select tasks with [cyan]Space[/cyan], then lifecycle keys or Optimize act on all of them",
    "Hide finished tasks with the exclusion search [cyan]!completed[/cyan]",
    "Press [cyan]S[/cyan] for the statistics dashboard",
]

# Bug reports and feedback
BUG_REPORT_INFO: str = """## Bug Reports & Feature Requests

Found a bug or have a feature request? Please report it to:

**GitHub Issues**: https://github.com/Kohei-Wada/taskdog/issues"""
