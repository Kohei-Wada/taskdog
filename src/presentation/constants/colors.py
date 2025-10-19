"""Color constants for presentation layer."""

from domain.entities.task import TaskStatus

# Message styles (colors)
STYLE_SUCCESS = "green"
STYLE_ERROR = "red"
STYLE_WARNING = "yellow"
STYLE_INFO = "cyan"

# Status color styles for rendering
STATUS_STYLES = {
    TaskStatus.PENDING: "yellow",
    TaskStatus.IN_PROGRESS: "blue",
    TaskStatus.COMPLETED: "green",
    TaskStatus.FAILED: "red",
    TaskStatus.ARCHIVED: "dim white",
}

# Status colors (bold) for special rendering
STATUS_COLORS_BOLD = {
    TaskStatus.PENDING: "yellow",
    TaskStatus.IN_PROGRESS: "bold blue",
    TaskStatus.COMPLETED: "bold green",
    TaskStatus.FAILED: "bold red",
    TaskStatus.ARCHIVED: "dim white",
}

# Gantt Chart Column Header Colors (Gantt-specific)
GANTT_COLUMN_EST_HOURS_COLOR = "yellow"

# Gantt Chart Day Header Colors
DAY_STYLE_SATURDAY = "blue"
DAY_STYLE_SUNDAY = "red"
DAY_STYLE_WEEKDAY = "cyan"
