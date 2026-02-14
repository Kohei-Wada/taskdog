# CLI Commands Reference

Complete reference for all Taskdog CLI commands.

## Table of Contents

- [Task Creation & Updates](#task-creation--updates)
- [Task Management](#task-management)
- [Dependencies](#dependencies)
- [Tags Management](#tags-management)
- [Time Tracking](#time-tracking)
- [Optimization](#optimization)
- [Visualization](#visualization)
- [Analytics](#analytics)
- [Notes & TUI](#notes--tui)
- [Task States](#task-states)
- [Tags](#tags)

## Task Creation & Updates

### add - Create a new task

```bash
taskdog add "Task name" [-p PRIORITY] [--fixed] [-d DEP_ID] [-t TAG]
```

Create a new task with optional priority, dependencies, and tags. Multiple `-d` and `-t` flags are allowed.

**Examples:**

```bash
taskdog add "Design phase" -p 150
taskdog add "Implementation" -p 100 -d 1 -t backend -t api
taskdog add "Team meeting" --fixed  # Won't be rescheduled
```

### update - Multi-field update

```bash
taskdog update ID [--name NAME] [--priority N] [--status STATUS] [--planned-start DATE] [--planned-end DATE] [--deadline DATE] [--estimated-duration HOURS]
```

Update multiple task fields at once.

**Examples:**

```bash
taskdog update 1 --priority 200 --deadline 2025-10-25
taskdog update 2 --name "New task name"
```

## Task Management

### start - Start tasks

```bash
taskdog start ID...
```

Start one or more tasks. Records actual start time and changes status to IN_PROGRESS.

**Examples:**

```bash
taskdog start 1
taskdog start 2 3 4  # Batch operation
```

### done - Complete tasks

```bash
taskdog done ID...
```

Mark tasks as completed. Records actual end time.

**Examples:**

```bash
taskdog done 1
taskdog done 2 3 4  # Batch operation
```

### pause - Pause tasks

```bash
taskdog pause ID...
```

Pause tasks and reset to PENDING status. Clears timestamps.

**Examples:**

```bash
taskdog pause 1
taskdog pause 2 3  # Batch operation
```

### cancel - Cancel tasks

```bash
taskdog cancel ID...
```

Mark tasks as CANCELED.

**Examples:**

```bash
taskdog cancel 1
taskdog cancel 2 3  # Batch operation
```

### reopen - Reopen tasks

```bash
taskdog reopen ID...
```

Reopen completed or canceled tasks. Resets to PENDING status.

**Examples:**

```bash
taskdog reopen 1
taskdog reopen 2 3  # Batch operation
```

### rm - Remove tasks

```bash
taskdog rm ID... [--hard]
```

Remove tasks. Default is soft delete (sets is_archived=true). Use `--hard` for permanent deletion.

**Examples:**

```bash
taskdog rm 1        # Soft delete (can be restored)
taskdog rm 2 --hard # Permanent deletion
```

### restore - Restore soft-deleted tasks

```bash
taskdog restore ID...
```

Restore previously archived (soft-deleted) tasks.

**Examples:**

```bash
taskdog restore 1
taskdog restore 2 3  # Batch operation
```

## Dependencies

### add-dependency - Add task dependency

```bash
taskdog add-dependency TASK_ID DEPENDS_ON_ID
```

Add a dependency relationship. Includes circular dependency detection.

**Examples:**

```bash
taskdog add-dependency 2 1  # Task 2 depends on task 1
```

### remove-dependency - Remove task dependency

```bash
taskdog remove-dependency TASK_ID DEP_ID
```

Remove a dependency relationship.

**Examples:**

```bash
taskdog remove-dependency 2 1
```

## Tags Management

### tags - Manage tags

```bash
taskdog tags              # List all tags with counts
taskdog tags ID           # Show tags for a task
taskdog tags ID TAG1...   # Set tags for a task (replaces existing)
```

**Examples:**

```bash
taskdog tags                    # List all tags
taskdog tags 1                  # Show task 1's tags
taskdog tags 1 urgent backend   # Set tags for task 1
```

## Optimization

### optimize - Auto-schedule tasks

```bash
taskdog optimize [--start-date DATE] [--max-hours-per-day N] [-a ALGORITHM] [-f]
```

Auto-generate optimal task schedules based on priorities, deadlines, and dependencies.

**Available Algorithms:**

- `greedy` (default) - Schedule highest priority tasks first
- `balanced` - Distribute workload evenly across days
- `backward` - Schedule from deadline backwards
- `priority_first` - Strict priority ordering
- `earliest_deadline` - Schedule tasks with earliest deadlines first
- `round_robin` - Rotate through tasks to minimize context switching
- `dependency_aware` - Prioritize tasks that unblock others
- `genetic` - Use genetic algorithm for optimization
- `monte_carlo` - Use Monte Carlo simulation

**Features:**

- Respects fixed tasks and dependencies
- Distributes workload across weekdays
- Avoids weekend scheduling
- Honors max_hours_per_day constraint

**Examples:**

```bash
taskdog optimize
taskdog optimize --start-date 2025-10-22 --max-hours-per-day 8
taskdog optimize -a balanced
taskdog optimize -f  # Force re-optimization
```

## Visualization

### table - Table view

```bash
taskdog table [OPTIONS]
```

Display tasks in table format with filtering and sorting.

**Options:**

- `-s/--sort FIELD` - Sort by: id, priority, deadline, name, status, planned_start
- `-r/--reverse` - Reverse sort order
- `-a/--all` - Include archived tasks (default: non-archived only)
- `-f/--fields LIST` - Custom field selection
- `--status STATUS` - Filter by status: pending, in_progress, completed, canceled
- `-t/--tag TAG` - Filter by tags (multiple tags use OR logic)
- `--start-date DATE` - Filter by planned start date (from)
- `--end-date DATE` - Filter by planned end date (to)

**Examples:**

```bash
taskdog table
taskdog table -s priority -r
taskdog table --status pending --tag backend
taskdog table -a  # Show archived tasks too
```

### gantt - Gantt chart

```bash
taskdog gantt [OPTIONS]
```

Display visual timeline with workload analysis. Supports same filter/sort options as table.

**Features:**

- Visual timeline with daily hours
- Status symbols (◆)
- Weekend coloring
- Workload summary
- Strikethrough for finished tasks

**Examples:**

```bash
taskdog gantt
taskdog gantt -s deadline
taskdog gantt --start-date 2025-10-20 --end-date 2025-10-30
```

### show - Task details

```bash
taskdog show ID [--raw]
```

Show detailed information for a task, including notes. Notes are rendered as markdown by default.

**Examples:**

```bash
taskdog show 1
taskdog show 1 --raw  # Show raw markdown
```

### export - Export tasks

```bash
taskdog export [OPTIONS]
```

Export tasks to JSON or CSV format. Exports non-archived tasks by default.

**Options:**

- `--format FORMAT` - json (default), csv, or markdown
- `-o/--output FILE` - Output file path
- `-f/--fields LIST` - Custom field selection
- `-a/--all` - Include archived tasks
- `--status STATUS` - Filter by status
- `-t/--tag TAG` - Filter by tags
- `--start-date DATE` - Filter by date range
- `--end-date DATE` - Filter by date range

**Examples:**

```bash
taskdog export
taskdog export --format csv -o tasks.csv
taskdog export --format markdown -o tasks.md
taskdog export --status pending -t backend
```

## Analytics

### stats - Task statistics

```bash
taskdog stats [--period PERIOD] [--focus FOCUS]
```

Display task statistics and analytics.

**Options:**

- `-p/--period` - all (default), 7d, 30d
- `-f/--focus` - all (default), basic, time, estimation, deadline, priority, trends

**Examples:**

```bash
taskdog stats
taskdog stats -p 7d -f time
taskdog stats --period 30d --focus trends
```

## Notes & TUI

### note - Edit task notes

```bash
taskdog note ID
```

Edit markdown notes for a task using `$EDITOR`.

**Examples:**

```bash
taskdog note 1
```

### tui - Interactive TUI

```bash
taskdog tui
```

Launch full-screen interactive terminal user interface.

**Key features:**

- Real-time task search and filtering
- Keyboard shortcuts for quick operations
- Sort by deadline, priority, planned start, or ID
- Visual status indicators with colors
- Task details panel with dependencies

See [Interactive TUI](../README.md#interactive-tui) section in README for full keyboard shortcuts.

## Task States

Tasks can be in one of four states:

- **PENDING**: Not started (yellow)
- **IN_PROGRESS**: Being worked on (blue)
- **COMPLETED**: Finished (green)
- **CANCELED**: Won't be done (red)

**Note**: Archived tasks (soft-deleted) retain their original status and can be restored with `taskdog restore`.

## Tags

Tasks can be organized with tags for better categorization and filtering.

**Examples:**

```bash
# Add task with tags
taskdog add "Backend API" --tag backend --tag api

# Manage tags
taskdog tags                    # List all tags with counts
taskdog tags 1                  # Show tags for task 1
taskdog tags 1 urgent backend   # Set tags (replaces existing)

# Filter by tags
taskdog table --tag backend     # Show tasks with 'backend' tag
taskdog table --tag api --tag db  # OR logic: tasks with 'api' OR 'db'
```

**Tag behavior:**

- Tags are case-sensitive
- Multiple tags can be assigned to a task
- Tags are automatically created when first used
- Filtering with multiple tags uses OR logic
- Empty or whitespace-only tags are not allowed
