"""Command provider for backup functionality."""

from __future__ import annotations

from taskdog.tui.palette.providers.base import SimpleSingleCommandProvider


class BackupCommandProvider(SimpleSingleCommandProvider):
    """Command provider for the 'Backup' command."""

    COMMAND_NAME = "Backup"
    COMMAND_HELP = "Back up the database to a file"
    COMMAND_CALLBACK_NAME = "run_backup"
