"""Delete task command for TUI."""

from application.dto.remove_task_input import RemoveTaskInput
from application.use_cases.remove_task import RemoveTaskUseCase
from presentation.tui.commands.base import TUICommandBase


class DeleteTaskCommand(TUICommandBase):
    """Command to delete the selected task.

    TODO: Add confirmation dialog before deletion.
    """

    def execute(self) -> None:
        """Execute the delete task command."""
        task = self.get_selected_task()
        if not task or task.id is None:
            self.notify_warning("No task selected")
            return

        # TODO: Add confirmation dialog
        try:
            use_case = RemoveTaskUseCase(self.repository)
            remove_input = RemoveTaskInput(task_id=task.id)
            use_case.execute(remove_input)
            self.reload_tasks()
            self.notify_success(f"Deleted task: {task.name} (ID: {task.id})")
        except Exception as e:
            self.notify_error("Error deleting task", e)
