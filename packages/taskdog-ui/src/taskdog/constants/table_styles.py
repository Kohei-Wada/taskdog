"""Table and panel style constants for presentation layer."""

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
COLUMN_STATUS_JUSTIFY = "center"
COLUMN_DATETIME_STYLE = "green"
COLUMN_DEADLINE_STYLE = "magenta"
COLUMN_DURATION_STYLE = "cyan"
COLUMN_FIELD_LABEL_STYLE = "cyan"  # For detail view field labels
COLUMN_NOTE_JUSTIFY = "center"

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
