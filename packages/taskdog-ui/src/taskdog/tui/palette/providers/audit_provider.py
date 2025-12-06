"""Command provider for audit log functionality."""

from __future__ import annotations

from taskdog.tui.palette.providers.base import SimpleSingleCommandProvider


class AuditCommandProvider(SimpleSingleCommandProvider):
    """Command provider for audit log panel toggle."""

    COMMAND_NAME = "Audit Logs"
    COMMAND_HELP = "Toggle audit log side panel"
    COMMAND_CALLBACK_NAME = "toggle_audit_panel"
