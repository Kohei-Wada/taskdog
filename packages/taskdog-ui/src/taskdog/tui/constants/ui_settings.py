"""UI settings and constants for TUI application.

This module centralizes all UI-related constants to improve maintainability
and avoid magic numbers scattered throughout the codebase.
"""

# Auto-refresh settings
AUTO_REFRESH_INTERVAL_SECONDS = 1.0
"""Interval in seconds for auto-refreshing elapsed time display."""

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
    "action_add_task": "add_task",
    "action_start_task": "start_task",
    "action_pause_task": "pause_task",
    "action_complete_task": "complete_task",
    "action_cancel_task": "cancel_task",
    "action_reopen_task": "reopen_task",
    "action_delete_task": "delete_task",
    "action_hard_delete_task": "hard_delete_task",
    "action_show_details": "show_details",
    "action_edit_task": "edit_task",
    "action_edit_note": "edit_note",
}
"""Mapping of Textual action names to command names for __getattr__ delegation."""
