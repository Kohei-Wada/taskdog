"""Symbol and background color constants for Gantt chart rendering."""

# Visual constants for Gantt chart symbols
SYMBOL_PLANNED = "░"
SYMBOL_EMPTY = " · "
SYMBOL_EMPTY_SPACE = "   "  # 3 spaces for planned background
SYMBOL_TODAY = "●"  # Today marker in date header

# Status-specific symbols for actual period (all single-width ASCII)
SYMBOL_PENDING = (
    "o"  # lowercase o - task not started yet (should not appear in actual period)
)
SYMBOL_IN_PROGRESS = "~"  # tilde - work in progress
SYMBOL_COMPLETED = "*"  # asterisk - task completed
SYMBOL_CANCELED = "x"  # lowercase x - task canceled

# UI Emojis
EMOJI_NOTE = "📝"  # Note indicator in task table

# Background colors for Gantt chart
BACKGROUND_COLOR = "rgb(100,100,100)"  # Weekday (allocated hours)
BACKGROUND_COLOR_SATURDAY = "rgb(100,100,150)"  # Saturday (blueish, allocated hours)
BACKGROUND_COLOR_SUNDAY = "rgb(150,100,100)"  # Sunday (reddish, allocated hours)
BACKGROUND_COLOR_HOLIDAY = "rgb(200,150,100)"  # Holiday (orange-ish, allocated hours)
BACKGROUND_COLOR_PLANNED_LIGHT = "rgb(60,60,60)"  # Planned period (no allocation yet)
BACKGROUND_COLOR_DEADLINE = "rgb(200,100,0)"  # Deadline (orange)
