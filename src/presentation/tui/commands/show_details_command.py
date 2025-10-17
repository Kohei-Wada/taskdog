"""Show details command for TUI."""

from presentation.tui.commands.base import TUICommandBase


class ShowDetailsCommand(TUICommandBase):
    """Command to show details of the selected task.

    TODO: Implement a dedicated detail view screen.
    Currently shows details in a notification.
    """

    def execute(self) -> None:
        """Execute the show details command."""
        task = self.get_selected_task()
        if not task:
            self.notify_warning("No task selected")
            return

        # For now, just show a notification with task details
        # Later we can implement a detailed view screen
        details = f"""
Task Details:
  ID: {task.id}
  Name: {task.name}
  Priority: {task.priority}
  Status: {task.status.value}
  Deadline: {task.deadline or 'Not set'}
  Estimated: {task.estimated_duration or 'Not set'}h
        """.strip()
        self.notify_success(details)
