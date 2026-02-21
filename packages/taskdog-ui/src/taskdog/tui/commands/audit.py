"""Audit command for TUI - toggles audit log screen."""

from taskdog.tui.commands.base import TUICommandBase
from taskdog.tui.screens.audit_log_screen import AuditLogScreen


class AuditCommand(TUICommandBase):
    """Command to toggle the audit log screen."""

    def execute_impl(self) -> None:
        """Toggle the audit log screen (push if not shown, pop if shown)."""
        if isinstance(self.app.screen, AuditLogScreen):
            self.app.pop_screen()
        else:
            self.app.push_screen(AuditLogScreen(api_client=self.context.api_client))
