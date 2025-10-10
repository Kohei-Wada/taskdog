"""Shared constants for task formatters."""

from domain.entities.task import TaskStatus

# Status style mappings for Rich formatting
STATUS_STYLES = {
    TaskStatus.PENDING: "yellow",
    TaskStatus.IN_PROGRESS: "blue",
    TaskStatus.COMPLETED: "green",
    TaskStatus.FAILED: "red",
}

# Status colors with bold modifiers for Gantt charts
STATUS_COLORS_BOLD = {
    TaskStatus.PENDING: "yellow",
    TaskStatus.IN_PROGRESS: "bold blue",
    TaskStatus.COMPLETED: "bold green",
    TaskStatus.FAILED: "bold red",
}

# Default datetime format used in task data
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
