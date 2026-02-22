"""Add task command for TUI."""

from taskdog.tui.commands.base import TUICommandBase
from taskdog.tui.dialogs.task_form_dialog import TaskFormDialog
from taskdog.tui.events import TaskCreated
from taskdog.tui.forms.task_form_fields import TaskFormData
from taskdog_core.domain.exceptions.task_exceptions import TaskError


class AddCommand(TUICommandBase):
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
            # (notification will be shown via WebSocket event)
            if task.id is None:
                raise ValueError("Created task must have an ID")
            self.app.post_message(TaskCreated(task.id))

        # Show task form dialog in add mode (no task parameter)
        # Wrap callback with error handling from base class
        input_defaults = (
            self.context.config.input_defaults if self.context.config else None
        )

        # Fetch existing tags for auto-completion (graceful degradation on failure)
        existing_tags: list[str] | None = None
        try:
            tag_stats = self.context.api_client.get_tag_statistics()
            existing_tags = list(tag_stats.tag_counts.keys())
        except TaskError:
            pass

        dialog = TaskFormDialog(
            input_defaults=input_defaults, existing_tags=existing_tags
        )
        self.app.push_screen(dialog, self.handle_error(handle_task_data))
