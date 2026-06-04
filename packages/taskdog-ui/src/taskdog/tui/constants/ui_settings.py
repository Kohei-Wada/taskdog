"""UI settings and constants for TUI application.

This module centralizes all UI-related constants to improve maintainability
and avoid magic numbers scattered throughout the codebase.

Note: UI input completion defaults (deadline_time, planned_start_time, etc.)
are now configurable via cli.toml [input_defaults] section and are accessed
through CliConfig.input_defaults, not from this module.
"""

__all__ = [
    "AUTO_REFRESH_INTERVAL_SECONDS",
    "MAX_HOURS_PER_DAY",
    "OPTIMIZATION_FAILURE_DETAIL_THRESHOLD",
    "RELOAD_DEBOUNCE_SECONDS",
    "SORT_KEY_LABELS",
    "TAGS_MAX_DISPLAY_LENGTH",
]

# Auto-refresh settings
AUTO_REFRESH_INTERVAL_SECONDS = 1.0
"""Interval in seconds for auto-refreshing elapsed time display."""

RELOAD_DEBOUNCE_SECONDS = 0.1
"""Debounce window for coalescing rapid task-list reload triggers.

A single change can fire both a local refresh and its WebSocket echo (and
batch operations fire many events); collapsing them within this window into
one reload avoids redundant full reloads."""

# Time validation constants
MAX_HOURS_PER_DAY = 24
"""Maximum number of hours per day for schedule optimization validation."""

# Optimization display settings
OPTIMIZATION_FAILURE_DETAIL_THRESHOLD = 5
"""Maximum number of failed tasks to display details for in optimization results."""

# Table display settings
TAGS_MAX_DISPLAY_LENGTH = 18
"""Maximum number of characters to display for tags in table view."""

# Sort key display labels
SORT_KEY_LABELS: dict[str, str] = {
    "deadline": "Deadline",
    "planned_start": "Planned Start",
    "priority": "Priority",
    "estimated_duration": "Duration",
    "id": "ID",
    "name": "Name",
    "status": "Status",
}
"""Mapping of sort keys to display labels for UI."""
