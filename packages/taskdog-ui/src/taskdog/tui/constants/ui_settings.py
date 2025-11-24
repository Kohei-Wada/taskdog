"""UI settings and constants for TUI application.

This module centralizes all UI-related constants to improve maintainability
and avoid magic numbers scattered throughout the codebase.
"""

# Auto-refresh settings
AUTO_REFRESH_INTERVAL_SECONDS = 1.0
"""Interval in seconds for auto-refreshing elapsed time display."""

# Time validation constants
MAX_HOURS_PER_DAY = 24
"""Maximum number of hours per day for schedule optimization validation."""

# Gantt chart display settings
DEFAULT_GANTT_DISPLAY_DAYS = 28
"""Default number of days to display in Gantt chart (4 weeks)."""

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

# Export format configuration
EXPORT_FORMAT_CONFIG: dict[str, dict[str, str]] = {
    "json": {"exporter_class": "JsonTaskExporter", "extension": "json"},
    "csv": {"exporter_class": "CsvTaskExporter", "extension": "csv"},
    "markdown": {"exporter_class": "MarkdownTableExporter", "extension": "md"},
}
"""Configuration for export formats including exporter class names and file extensions."""

# Action to command mapping for dynamic action handling
ACTION_TO_COMMAND_MAP: dict[str, str] = {
    "action_refresh": "refresh",
    "action_add": "add",
    "action_start": "start",
    "action_pause": "pause",
    "action_done": "done",
    "action_cancel": "cancel",
    "action_reopen": "reopen",
    "action_rm": "rm",
    "action_hard_delete": "hard_delete",
    "action_show": "show",
    "action_edit": "edit",
    "action_note": "note",
    "action_show_help": "show_help",
}
"""Mapping of Textual action names to command names for __getattr__ delegation."""

# Task form default values
DEFAULT_TASK_PRIORITY = 5
"""Default priority for new tasks in the form dialog."""

DEFAULT_BUSINESS_START_HOUR = 9
"""Default business day start hour (9 AM) for task scheduling."""

DEFAULT_BUSINESS_END_HOUR = 18
"""Default business day end hour (6 PM) for task scheduling."""
