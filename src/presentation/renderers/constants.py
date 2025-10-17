"""Shared constants for task formatters.

DEPRECATED: This module is deprecated. Use presentation.constants instead.
This module is kept for backward compatibility and re-exports from the new location.
"""

from domain.constants import DATETIME_FORMAT

# Re-export from new constants location for backward compatibility
from presentation.constants.colors import STATUS_COLORS_BOLD, STATUS_STYLES

__all__ = ["DATETIME_FORMAT", "STATUS_COLORS_BOLD", "STATUS_STYLES"]
