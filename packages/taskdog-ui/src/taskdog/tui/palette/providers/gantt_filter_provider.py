"""Command provider for toggling the Gantt chart search filter."""

from __future__ import annotations

from taskdog.tui.palette.providers.base import SimpleSingleCommandProvider


class GanttFilterCommandProvider(SimpleSingleCommandProvider):
    """Command provider for toggling the Gantt chart search filter."""

    COMMAND_NAME = "Toggle Gantt Filter"
    COMMAND_HELP = "Toggle search filter for Gantt chart"
    COMMAND_CALLBACK_NAME = "action_toggle_gantt_filter"
