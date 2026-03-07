"""Gantt chart constants (CLI/TUI shared)."""

from taskdog.constants.common import JustifyValue

# Gantt-specific headers
HEADER_TIMELINE = "Timeline"
GANTT_WORKLOAD_LABEL = "Est. Workload[h]"

# Gantt Chart Column Widths (CLI)
GANTT_TABLE_ID_WIDTH = 4
GANTT_TABLE_TASK_MIN_WIDTH = 20
GANTT_TABLE_EST_HOURS_WIDTH = 7

# Gantt Chart Timeline Dimensions
MIN_TIMELINE_WIDTH = 30
CHARS_PER_DAY = 3
# Fixed columns overhead for CLI Gantt: ID(4) + Name(30) + Est(7) + padding(8) + borders(5)
GANTT_CLI_FIXED_COLUMNS_WIDTH = 54

# Gantt Widget Dimensions (TUI)
DEFAULT_GANTT_WIDGET_WIDTH = 120
MIN_CONSOLE_WIDTH = 80
BORDER_WIDTH = 2
MIN_GANTT_DISPLAY_DAYS = 91

# Gantt-specific colors
GANTT_COLUMN_EST_HOURS_COLOR = "yellow"
DAY_STYLE_SATURDAY = "blue"
DAY_STYLE_SUNDAY = "red"
DAY_STYLE_WEEKDAY = "cyan"

# Gantt-specific justify
JUSTIFY_ESTIMATED_GANTT: JustifyValue = "center"
