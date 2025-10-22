"""Symbol and background color constants for Gantt chart rendering."""

# Visual constants for Gantt chart symbols
SYMBOL_PLANNED = "░"
SYMBOL_ACTUAL = "◆"
SYMBOL_EMPTY = " · "
SYMBOL_EMPTY_SPACE = "   "  # 3 spaces for planned background
SYMBOL_TODAY = "●"  # Today marker in date header

# UI Emojis
EMOJI_NOTE = "📝"  # Note indicator in task table

# Background colors for Gantt chart
BACKGROUND_COLOR = "rgb(100,100,100)"  # Weekday
BACKGROUND_COLOR_SATURDAY = "rgb(100,100,150)"  # Saturday (blueish)
BACKGROUND_COLOR_SUNDAY = "rgb(150,100,100)"  # Sunday (reddish)
BACKGROUND_COLOR_HOLIDAY = "rgb(200,150,100)"  # Holiday (orange-ish)
BACKGROUND_COLOR_DEADLINE = "rgb(200,100,0)"  # Deadline (orange)
