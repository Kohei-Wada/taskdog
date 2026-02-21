"""Command provider for audit log functionality."""

from __future__ import annotations

from taskdog.tui.palette.providers.base import SimpleSingleCommandProvider


class AuditCommandProvider(SimpleSingleCommandProvider):
    """Command provider for audit log screen."""

    COMMAND_NAME = "Audit Logs"
    COMMAND_HELP = "Toggle audit log screen"
    COMMAND_CALLBACK_NAME = "show_audit_logs"
