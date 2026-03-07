"""Common constants shared across multiple features."""

from typing import Literal

# Type alias for justify values
JustifyValue = Literal["left", "center", "right"]

# Table basic styles (used by RichTableRenderer and RichGanttRenderer)
TABLE_HEADER_STYLE = "bold magenta"
TABLE_BORDER_STYLE = "bright_blue"
TABLE_PADDING = (0, 1)
TABLE_TITLE_COLOR = "bold cyan"

# Panel styles (used by RichDetailRenderer)
PANEL_BORDER_STYLE_PRIMARY = "cyan"
PANEL_BORDER_STYLE_SECONDARY = "dim"

# Finished task style (used across all renderers)
COLUMN_FINISHED_STYLE = "strike dim"

# Detail view field label style
COLUMN_FIELD_LABEL_STYLE = "cyan"

# Datetime formatting
COLUMN_DATETIME_NO_WRAP = True

# Shared column headers (used by gantt + task_table)
HEADER_ID = "ID"
HEADER_NAME = "Name"
HEADER_ESTIMATED = "Estimated[h]"

# Shared column styles (used by gantt + task_table + timeline)
COLUMN_ID_STYLE = "cyan"
COLUMN_NAME_STYLE = "white"

# Shared column justify (used by gantt + task_table)
JUSTIFY_ID: JustifyValue = "center"
JUSTIFY_NAME: JustifyValue = "left"
JUSTIFY_ESTIMATED: JustifyValue = "center"
