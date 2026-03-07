"""Presentation layer constants.

This module re-exports cross-cutting constants (colors, icons, symbols, common).
Feature-specific constants should be imported directly from their modules:
  - taskdog.constants.gantt
  - taskdog.constants.task_table
  - taskdog.constants.audit_log
  - taskdog.constants.timeline
"""

# Re-export color constants
from taskdog.constants.colors import (
    BACKGROUND_COLOR,
    BACKGROUND_COLOR_DEADLINE,
    BACKGROUND_COLOR_SATURDAY,
    BACKGROUND_COLOR_SUNDAY,
    STATUS_COLORS_BOLD,
    STATUS_STYLES,
    STYLE_ERROR,
    STYLE_INFO,
    STYLE_SUCCESS,
    STYLE_WARNING,
)

# Re-export common constants
from taskdog.constants.common import (
    COLUMN_DATETIME_NO_WRAP,
    COLUMN_FIELD_LABEL_STYLE,
    COLUMN_FINISHED_STYLE,
    COLUMN_ID_STYLE,
    COLUMN_NAME_STYLE,
    JUSTIFY_ESTIMATED,
    JUSTIFY_ID,
    JUSTIFY_NAME,
    PANEL_BORDER_STYLE_PRIMARY,
    PANEL_BORDER_STYLE_SECONDARY,
    TABLE_BORDER_STYLE,
    TABLE_HEADER_STYLE,
    TABLE_PADDING,
    TABLE_TITLE_COLOR,
)

# Re-export formatting utility
from taskdog.constants.formatting import format_table_title

# Re-export icon constants
from taskdog.constants.icons import (
    ICON_ERROR,
    ICON_INFO,
    ICON_SUCCESS,
    ICON_WARNING,
)

# Re-export symbol constants
from taskdog.constants.symbols import (
    SYMBOL_CANCELED,
    SYMBOL_COMPLETED,
    SYMBOL_EMPTY,
    SYMBOL_EMPTY_SPACE,
    SYMBOL_IN_PROGRESS,
    SYMBOL_PENDING,
    SYMBOL_PLANNED,
)

__all__ = [
    "BACKGROUND_COLOR",
    "BACKGROUND_COLOR_DEADLINE",
    "BACKGROUND_COLOR_SATURDAY",
    "BACKGROUND_COLOR_SUNDAY",
    "COLUMN_DATETIME_NO_WRAP",
    "COLUMN_FIELD_LABEL_STYLE",
    "COLUMN_FINISHED_STYLE",
    "COLUMN_ID_STYLE",
    "COLUMN_NAME_STYLE",
    "ICON_ERROR",
    "ICON_INFO",
    "ICON_SUCCESS",
    "ICON_WARNING",
    "JUSTIFY_ESTIMATED",
    "JUSTIFY_ID",
    "JUSTIFY_NAME",
    "PANEL_BORDER_STYLE_PRIMARY",
    "PANEL_BORDER_STYLE_SECONDARY",
    "STATUS_COLORS_BOLD",
    "STATUS_STYLES",
    "STYLE_ERROR",
    "STYLE_INFO",
    "STYLE_SUCCESS",
    "STYLE_WARNING",
    "SYMBOL_CANCELED",
    "SYMBOL_COMPLETED",
    "SYMBOL_EMPTY",
    "SYMBOL_EMPTY_SPACE",
    "SYMBOL_IN_PROGRESS",
    "SYMBOL_PENDING",
    "SYMBOL_PLANNED",
    "TABLE_BORDER_STYLE",
    "TABLE_HEADER_STYLE",
    "TABLE_PADDING",
    "TABLE_TITLE_COLOR",
    "format_table_title",
]
