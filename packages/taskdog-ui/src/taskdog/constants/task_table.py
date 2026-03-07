"""Task table constants (CLI/TUI shared)."""

from taskdog.constants.common import JustifyValue

# Task Table headers
HEADER_STATUS = "Status"
HEADER_PRIORITY = "Priority"
HEADER_FLAGS = "Flags"
HEADER_ACTUAL = "Actual[h]"
HEADER_DEADLINE = "Deadline"
HEADER_PLANNED_START = "Planned Start"
HEADER_PLANNED_END = "Planned End"
HEADER_ACTUAL_START = "Actual Start"
HEADER_ACTUAL_END = "Actual End"
HEADER_ELAPSED = "Elapsed"
HEADER_DEPENDENCIES = "Dependencies"
HEADER_TAGS = "Tags"
HEADER_NOTE = "Note"
HEADER_FIXED = "Fixed"
HEADER_DURATION = "Duration"
HEADER_CREATED_AT = "Created At"
HEADER_UPDATED_AT = "Updated At"

# Task Table Display Limits
TASK_NAME_COLUMN_WIDTH = 30
STATUS_COLUMN_WIDTH = 13
ESTIMATED_COLUMN_WIDTH = 14
PAGE_SCROLL_SIZE = 10

# Task table column styles
COLUMN_PRIORITY_STYLE = "yellow"
COLUMN_DATETIME_STYLE = "green"
COLUMN_DEADLINE_STYLE = "magenta"
COLUMN_DURATION_STYLE = "cyan"
COLUMN_ELAPSED_STYLE = "cyan"
COLUMN_CREATED_AT_STYLE = "dim"
COLUMN_UPDATED_AT_STYLE = "dim"
COLUMN_DEPENDENCIES_STYLE = "cyan"
COLUMN_FIXED_STYLE = "yellow"
COLUMN_TAGS_STYLE = "magenta"

# Task table column justify
JUSTIFY_STATUS: JustifyValue = "center"
JUSTIFY_PRIORITY: JustifyValue = "center"
JUSTIFY_FLAGS: JustifyValue = "center"
JUSTIFY_ACTUAL: JustifyValue = "center"
JUSTIFY_DEADLINE: JustifyValue = "center"
JUSTIFY_PLANNED_START: JustifyValue = "center"
JUSTIFY_PLANNED_END: JustifyValue = "center"
JUSTIFY_ACTUAL_START: JustifyValue = "center"
JUSTIFY_ACTUAL_END: JustifyValue = "center"
JUSTIFY_ELAPSED: JustifyValue = "center"
JUSTIFY_DEPENDENCIES: JustifyValue = "center"
JUSTIFY_TAGS: JustifyValue = "center"
JUSTIFY_NOTE: JustifyValue = "center"
JUSTIFY_FIXED: JustifyValue = "center"
JUSTIFY_DURATION: JustifyValue = "right"
JUSTIFY_CREATED_AT: JustifyValue = "center"
JUSTIFY_UPDATED_AT: JustifyValue = "center"
