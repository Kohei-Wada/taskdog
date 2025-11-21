"""Help content for TUI help screen.

This module provides content for the help screen including
basic usage, workflow guidance, and feature explanations.
"""

# Basic workflow guide
BASIC_WORKFLOW: str = """**Getting Started with Taskdog TUI**

1. **Add a Task**: Press 'a' to create a new task
   - Set priority, deadline, estimated duration
   - Add dependencies and tags if needed

2. **Start Working**: Press 's' on a task to start it
   - Status changes to IN_PROGRESS
   - Actual start time is recorded

3. **Complete Task**: Press 'd' when done
   - Status changes to COMPLETED
   - Actual end time is recorded

4. **View Details**: Press 'i' to see full task information
   - Shows schedule, actual tracking, and notes"""

# Main features explanation
MAIN_FEATURES: str = """**Key Features**

• **Task Table**: Main view showing all your tasks
  - Use j/k or arrow keys to navigate
  - Press 't' to toggle completed/canceled tasks

• **Gantt Chart**: Visual timeline of your tasks
  - Shows task schedules and workload per day
  - Use Ctrl+J/K to switch between table and gantt

• **Search**: Press '/' to filter tasks by name
  - Supports regex patterns
  - Press Escape to clear search

• **Notes**: Press 'v' to edit markdown notes for any task
  - Opens your $EDITOR (vim, nano, etc.)"""

# Command palette explanation
COMMAND_PALETTE_INFO: str = """**Command Palette (Ctrl+P or Ctrl+\\)**

The command palette gives you access to:

• **Sort**: Change task sorting order
  - Sort by deadline, priority, status, name, etc.

• **Optimize**: Run schedule optimization
  - Multiple algorithms available (greedy, balanced, etc.)

• **Export**: Export tasks to JSON, CSV, or Markdown

• **Keys**: View all keyboard shortcuts
  - Complete list of keybindings with descriptions

**Tip**: Type to search, then press Enter to execute"""

# Quick tips for new users
QUICK_TIPS: list[str] = [
    "Press Ctrl+P then type 'Keys' to see all keyboard shortcuts",
    "Use 'a' → 's' → 'd' workflow for quick task management",
    "Edit task details with 'e', add notes with 'v'",
    "Archive tasks with 'x' (soft delete), restore them later",
    "Press 'i' to see full task details including notes",
    "Use '/' for quick search, Escape to clear",
]
