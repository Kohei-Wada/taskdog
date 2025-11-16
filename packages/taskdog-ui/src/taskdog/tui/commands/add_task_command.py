"""Add task command for TUI."""

from taskdog.tui.commands.base import TUICommandBase
from taskdog.tui.commands.registry import command_registry
from taskdog.tui.events import TaskCreated
from taskdog.tui.forms.task_form_fields import TaskFormData
from taskdog.tui.messages import TUIMessageBuilder
from taskdog.tui.screens.task_form_dialog import TaskFormDialog


@command_registry.register("add_task")
class AddTaskCommand(TUICommandBase):
    """Command to add a new task with input dialog."""

    def execute(self) -> None:
        """Execute the add task command."""

        def handle_task_data(form_data: TaskFormData | None) -> None:
            """Handle the task data from the dialog.

            Args:
                form_data: Form data or None if cancelled
            """
            if form_data is None:
                return  # User cancelled

            # Create task via API client using TaskFormData helper methods
            task = self.context.api_client.create_task(
                name=form_data.name,
                priority=form_data.priority,
                deadline=form_data.get_deadline(),
                estimated_duration=form_data.estimated_duration,
                planned_start=form_data.get_planned_start(),
                planned_end=form_data.get_planned_end(),
                is_fixed=form_data.is_fixed,
                tags=form_data.tags,
            )

            # Add dependencies if specified
            if form_data.depends_on and task.id is not None:
                failed_operations = self.manage_dependencies(
                    task.id, add_deps=form_data.depends_on
                )
                if failed_operations:
                    self.notify_warning(
                        "Task created but some dependencies failed:\n"
                        + "\n".join(failed_operations)
                    )

            # Post TaskCreated event to trigger UI refresh
            if task.id is None:
                raise ValueError("Created task must have an ID")
            self.app.post_message(TaskCreated(task.id))
            msg = TUIMessageBuilder.task_action("Added task", task.name, task.id)
            self.notify_success(msg)

        # Show task form dialog in add mode (no task parameter)
        # Wrap callback with error handling from base class
        dialog = TaskFormDialog(config=self.context.config)
        self.app.push_screen(dialog, self.handle_error(handle_task_data))
