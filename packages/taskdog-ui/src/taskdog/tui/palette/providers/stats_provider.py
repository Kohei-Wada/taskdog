"""Command provider for statistics functionality."""

from __future__ import annotations

from taskdog.tui.palette.providers.base import SimpleSingleCommandProvider


class StatsCommandProvider(SimpleSingleCommandProvider):
    """Command provider for stats command."""

    COMMAND_NAME = "Stats"
    COMMAND_HELP = "Show the statistics dashboard"
    COMMAND_CALLBACK_NAME = "search_stats"
