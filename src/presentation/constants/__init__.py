"""Presentation layer constants.

This module provides convenient re-exports of all presentation constants.
"""

# Re-export color constants
from presentation.constants.colors import (
    STATUS_COLORS_BOLD,
    STATUS_STYLES,
    STYLE_ERROR,
    STYLE_INFO,
    STYLE_SUCCESS,
    STYLE_WARNING,
)

# Re-export icon constants
from presentation.constants.icons import (
    ICON_ERROR,
    ICON_INFO,
    ICON_SUCCESS,
    ICON_WARNING,
)

# Re-export symbol constants
from presentation.constants.symbols import (
    BACKGROUND_COLOR,
    BACKGROUND_COLOR_DEADLINE,
    BACKGROUND_COLOR_SATURDAY,
    BACKGROUND_COLOR_SUNDAY,
    SYMBOL_CANCELED,
    SYMBOL_COMPLETED,
    SYMBOL_EMPTY,
    SYMBOL_EMPTY_SPACE,
    SYMBOL_IN_PROGRESS,
    SYMBOL_PENDING,
    SYMBOL_PLANNED,
)

# Re-export table style constants
from presentation.constants.table_styles import (
    COLUMN_DATETIME_NO_WRAP,
    COLUMN_DATETIME_STYLE,
    COLUMN_DEADLINE_STYLE,
    COLUMN_DURATION_STYLE,
    COLUMN_FIELD_LABEL_STYLE,
    COLUMN_ID_STYLE,
    COLUMN_NAME_STYLE,
    COLUMN_NOTE_JUSTIFY,
    COLUMN_PRIORITY_STYLE,
    COLUMN_STATUS_JUSTIFY,
    PANEL_BORDER_STYLE_PRIMARY,
    PANEL_BORDER_STYLE_SECONDARY,
    TABLE_BORDER_STYLE,
    TABLE_HEADER_STYLE,
    TABLE_PADDING,
    TABLE_TITLE_COLOR,
    format_table_title,
)

__all__ = [
    # Background colors
    "BACKGROUND_COLOR",
    "BACKGROUND_COLOR_DEADLINE",
    "BACKGROUND_COLOR_SATURDAY",
    "BACKGROUND_COLOR_SUNDAY",
    # Column styles
    "COLUMN_DATETIME_NO_WRAP",
    "COLUMN_DATETIME_STYLE",
    "COLUMN_DEADLINE_STYLE",
    "COLUMN_DURATION_STYLE",
    "COLUMN_FIELD_LABEL_STYLE",
    "COLUMN_ID_STYLE",
    "COLUMN_NAME_STYLE",
    "COLUMN_NOTE_JUSTIFY",
    "COLUMN_PRIORITY_STYLE",
    "COLUMN_STATUS_JUSTIFY",
    # Icons
    "ICON_ERROR",
    "ICON_INFO",
    "ICON_SUCCESS",
    "ICON_WARNING",
    # Panel styles
    "PANEL_BORDER_STYLE_PRIMARY",
    "PANEL_BORDER_STYLE_SECONDARY",
    # Status styles
    "STATUS_COLORS_BOLD",
    "STATUS_STYLES",
    # Message styles
    "STYLE_ERROR",
    "STYLE_INFO",
    "STYLE_SUCCESS",
    "STYLE_WARNING",
    # Symbols
    "SYMBOL_CANCELED",
    "SYMBOL_COMPLETED",
    "SYMBOL_EMPTY",
    "SYMBOL_EMPTY_SPACE",
    "SYMBOL_IN_PROGRESS",
    "SYMBOL_PENDING",
    "SYMBOL_PLANNED",
    # Table styles
    "TABLE_BORDER_STYLE",
    "TABLE_HEADER_STYLE",
    "TABLE_PADDING",
    "TABLE_TITLE_COLOR",
    # Functions
    "format_table_title",
]
