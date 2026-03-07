"""Table and panel style constants for presentation layer."""

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

# Common column styles (used across all renderers)
COLUMN_ID_STYLE = "cyan"
COLUMN_NAME_STYLE = "white"
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
COLUMN_FINISHED_STYLE = "strike dim"
COLUMN_FIELD_LABEL_STYLE = "cyan"  # For detail view field labels

# Column justify (shared between CLI and TUI)
JUSTIFY_ID: JustifyValue = "center"
JUSTIFY_NAME: JustifyValue = "left"
JUSTIFY_STATUS: JustifyValue = "center"
JUSTIFY_PRIORITY: JustifyValue = "center"
JUSTIFY_FLAGS: JustifyValue = "center"
JUSTIFY_ESTIMATED: JustifyValue = "center"
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

# Audit log column styles
COLUMN_AUDIT_ID_STYLE = "dim"
COLUMN_AUDIT_STATUS_OK_STYLE = "green"
COLUMN_AUDIT_STATUS_FAIL_STYLE = "red"

# Audit log column justify
JUSTIFY_AUDIT_TIMESTAMP: JustifyValue = "center"
JUSTIFY_AUDIT_ID: JustifyValue = "center"
JUSTIFY_AUDIT_NAME: JustifyValue = "left"
JUSTIFY_AUDIT_OPERATION: JustifyValue = "center"
JUSTIFY_AUDIT_CHANGES: JustifyValue = "left"
JUSTIFY_AUDIT_CLIENT: JustifyValue = "center"
JUSTIFY_AUDIT_STATUS: JustifyValue = "center"
JUSTIFY_AUDIT_RESOURCE: JustifyValue = "left"

# Datetime formatting
COLUMN_DATETIME_NO_WRAP = True


def format_table_title(title: str) -> str:
    """Format table title with standard styling.

    Args:
        title: The title text to format

    Returns:
        Formatted title string with Rich markup
    """
    return f"[{TABLE_TITLE_COLOR}]{title}[/{TABLE_TITLE_COLOR}]"
