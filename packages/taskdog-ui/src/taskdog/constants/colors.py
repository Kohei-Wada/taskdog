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

# Background colors for Gantt chart
BACKGROUND_COLOR = "rgb(100,100,100)"  # Weekday (allocated hours)
BACKGROUND_COLOR_SATURDAY = "rgb(100,100,150)"  # Saturday (blueish, allocated hours)
BACKGROUND_COLOR_SUNDAY = "rgb(150,100,100)"  # Sunday (reddish, allocated hours)
BACKGROUND_COLOR_HOLIDAY = "rgb(200,150,100)"  # Holiday (orange-ish, allocated hours)
BACKGROUND_COLOR_PLANNED_LIGHT = "rgb(60,60,60)"  # Planned period (no allocation yet)
BACKGROUND_COLOR_DEADLINE = "rgb(200,100,0)"  # Deadline (orange)
