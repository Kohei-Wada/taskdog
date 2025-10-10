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
    SYMBOL_ACTUAL,
    SYMBOL_EMPTY,
    SYMBOL_EMPTY_SPACE,
    SYMBOL_PLANNED,
)

__all__ = [
    # Symbols
    "BACKGROUND_COLOR",
    "BACKGROUND_COLOR_DEADLINE",
    "BACKGROUND_COLOR_SATURDAY",
    "BACKGROUND_COLOR_SUNDAY",
    # Icons
    "ICON_ERROR",
    "ICON_INFO",
    "ICON_SUCCESS",
    "ICON_WARNING",
    # Colors
    "STATUS_COLORS_BOLD",
    "STATUS_STYLES",
    "STYLE_ERROR",
    "STYLE_INFO",
    "STYLE_SUCCESS",
    "STYLE_WARNING",
    "SYMBOL_ACTUAL",
    "SYMBOL_EMPTY",
    "SYMBOL_EMPTY_SPACE",
    "SYMBOL_PLANNED",
]
