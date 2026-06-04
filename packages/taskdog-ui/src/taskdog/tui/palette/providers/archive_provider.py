"""Command provider for toggling archived task visibility."""

from __future__ import annotations

from taskdog.tui.palette.providers.base import SimpleSingleCommandProvider


class ArchiveCommandProvider(SimpleSingleCommandProvider):
    """Command provider for toggling archived tasks in the task list."""

    COMMAND_NAME = "Toggle Archive"
    COMMAND_HELP = "Show or hide archived tasks in the task list"
    COMMAND_CALLBACK_NAME = "toggle_archive"
