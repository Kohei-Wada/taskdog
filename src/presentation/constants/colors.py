"""Color constants for presentation layer."""

# Message styles (colors)
STYLE_SUCCESS = "green"
STYLE_ERROR = "red"
STYLE_WARNING = "yellow"
STYLE_INFO = "cyan"

# Status color styles for rendering
# Note: Uses string keys to support both domain and presentation TaskStatus enums
STATUS_STYLES = {
    "PENDING": "yellow",
    "IN_PROGRESS": "blue",
    "COMPLETED": "green",
    "CANCELED": "red",
}

# Status colors (bold) for special rendering
# Note: Uses string keys to support both domain and presentation TaskStatus enums
STATUS_COLORS_BOLD = {
    "PENDING": "yellow",
    "IN_PROGRESS": "bold blue",
    "COMPLETED": "bold green",
    "CANCELED": "bold red",
}

# Gantt Chart Column Header Colors (Gantt-specific)
GANTT_COLUMN_EST_HOURS_COLOR = "yellow"

# Gantt Chart Day Header Colors
DAY_STYLE_SATURDAY = "blue"
DAY_STYLE_SUNDAY = "red"
DAY_STYLE_WEEKDAY = "cyan"
