"""Shared constants for task formatters."""

from domain.constants import DATETIME_FORMAT
from domain.entities.task import TaskStatus

# Status style mappings for Rich formatting
STATUS_STYLES = {
    TaskStatus.PENDING: "yellow",
    TaskStatus.IN_PROGRESS: "blue",
    TaskStatus.COMPLETED: "green",
    TaskStatus.FAILED: "red",
    TaskStatus.ARCHIVED: "dim white",
}

# Status colors with bold modifiers for Gantt charts
STATUS_COLORS_BOLD = {
    TaskStatus.PENDING: "yellow",
    TaskStatus.IN_PROGRESS: "bold blue",
    TaskStatus.COMPLETED: "bold green",
    TaskStatus.FAILED: "bold red",
    TaskStatus.ARCHIVED: "dim white",
}

# Re-export DATETIME_FORMAT for backward compatibility
__all__ = ["DATETIME_FORMAT", "STATUS_COLORS_BOLD", "STATUS_STYLES"]
