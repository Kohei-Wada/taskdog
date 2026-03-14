"""Command providers for optimization functionality."""

from __future__ import annotations

from taskdog.tui.palette.providers.base import SimpleSingleCommandProvider


class OptimizeCommandProvider(SimpleSingleCommandProvider):
    """Command provider for optimization commands."""

    COMMAND_NAME = "Optimize"
    COMMAND_HELP = "Optimize schedule with selected algorithm"
    COMMAND_CALLBACK_NAME = "search_optimize"
