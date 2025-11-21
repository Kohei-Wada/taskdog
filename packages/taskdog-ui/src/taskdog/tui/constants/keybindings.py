"""Keybinding metadata for TUI help documentation.

This module provides a single source of truth for all keybindings
displayed in the help screen and footer.
"""

from typing import TypedDict


class KeyBinding(TypedDict):
    """Type definition for a keybinding entry."""

    key: str
    action: str
    description: str


# Categorized keybindings for help screen
KEYBINDINGS_BY_CATEGORY: dict[str, list[KeyBinding]] = {
    "Navigation": [
        {
            "key": "j / ↓",
            "action": "Move Down",
            "description": "Move cursor to the next task in the list",
        },
        {
            "key": "k / ↑",
            "action": "Move Up",
            "description": "Move cursor to the previous task in the list",
        },
        {
            "key": "Ctrl+J",
            "action": "Switch Widget Down",
            "description": "Move focus to the next widget (table → gantt chart)",
        },
        {
            "key": "Ctrl+K",
            "action": "Switch Widget Up",
            "description": "Move focus to the previous widget (gantt chart → table)",
        },
        {
            "key": "/",
            "action": "Search",
            "description": "Search for tasks by name (regex supported)",
        },
        {
            "key": "Escape",
            "action": "Clear Search",
            "description": "Clear the search filter and show all tasks",
        },
    ],
    "Task Operations": [
        {
            "key": "a",
            "action": "Add Task",
            "description": "Create a new task with priority, dependencies, and tags",
        },
        {
            "key": "s",
            "action": "Start Task",
            "description": "Start the selected task (sets status to IN_PROGRESS)",
        },
        {
            "key": "d",
            "action": "Mark Done",
            "description": "Mark the selected task as completed",
        },
        {
            "key": "P",
            "action": "Pause Task",
            "description": "Pause the selected task and reset to PENDING status",
        },
        {
            "key": "c",
            "action": "Cancel Task",
            "description": "Cancel the selected task",
        },
        {
            "key": "R",
            "action": "Reopen Task",
            "description": "Reopen a completed or canceled task",
        },
    ],
    "Modification": [
        {
            "key": "e",
            "action": "Edit Task",
            "description": "Edit task properties (name, priority, deadline, etc.)",
        },
        {
            "key": "v",
            "action": "Edit Note",
            "description": "Edit markdown notes for the selected task",
        },
        {
            "key": "x",
            "action": "Archive Task",
            "description": "Archive the selected task (soft delete, can be restored)",
        },
        {
            "key": "X",
            "action": "Delete Task",
            "description": "Permanently delete the selected task (cannot be undone)",
        },
    ],
    "View & Display": [
        {
            "key": "t",
            "action": "Toggle Completed",
            "description": "Toggle visibility of completed and canceled tasks",
        },
        {
            "key": "Ctrl+T",
            "action": "Toggle Sort",
            "description": "Toggle sort direction (ascending ⇔ descending)",
        },
        {
            "key": "r",
            "action": "Refresh",
            "description": "Refresh the task list from the server",
        },
        {
            "key": "i",
            "action": "Show Details",
            "description": "Show detailed information about the selected task",
        },
    ],
    "System": [
        {
            "key": "?",
            "action": "Show Help",
            "description": "Display this help screen with keybindings",
        },
        {
            "key": "Ctrl+P / Ctrl+\\",
            "action": "Command Palette",
            "description": "Open command palette for sort, optimize, export commands",
        },
        {
            "key": "q",
            "action": "Quit",
            "description": "Quit the app and return to the command prompt",
        },
    ],
}

# Quick start tips for new users
QUICK_START_TIPS: list[str] = [
    "Add a task with 'a', then start it with 's', and mark done with 'd'",
    "Use Ctrl+P to access the command palette for sort, optimize, and export",
    "Press '/' to search tasks by name (supports regex patterns)",
    "Use Ctrl+J/K to switch between the task table and Gantt chart",
    "Press 't' to toggle visibility of completed and canceled tasks",
    "Hover over any keybinding in the footer for a tooltip",
]

# Command palette explanation
COMMAND_PALETTE_INFO: str = """The Command Palette (Ctrl+P) provides access to additional commands:

• Sort: Change task sorting (deadline, priority, status, name, created_at)
• Optimize: Run schedule optimization with various algorithms
• Export: Export tasks to JSON or CSV format

Type to search for commands, then select with Enter."""

# Search usage explanation
SEARCH_USAGE_INFO: str = """Search (/) lets you filter tasks by name:

• Type any text to filter tasks
• Supports regex patterns (e.g., "bug.*fix" matches "bug fix", "bugfix", etc.)
• Press Escape to clear the search and show all tasks
• Search is case-insensitive by default"""


# Category display order for help screen
CATEGORY_ORDER: list[str] = [
    "Navigation",
    "Task Operations",
    "Modification",
    "View & Display",
    "System",
]
