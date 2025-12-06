"""Audit command for TUI - toggles audit log side panel."""

from taskdog.tui.commands.base import TUICommandBase


class AuditCommand(TUICommandBase):
    """Command to toggle the audit log side panel visibility."""

    def execute_impl(self) -> None:
        """Execute the audit toggle command."""
        if self.app.main_screen:
            self.app.main_screen.toggle_audit_panel()
