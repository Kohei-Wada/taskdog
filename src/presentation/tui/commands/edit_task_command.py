"""Edit task command for TUI."""

from application.dto.manage_dependencies_input import AddDependencyInput, RemoveDependencyInput
from application.dto.update_task_input import UpdateTaskInput
from application.use_cases.add_dependency import AddDependencyUseCase
from application.use_cases.remove_dependency import RemoveDependencyUseCase
from application.use_cases.update_task import UpdateTaskUseCase
from domain.exceptions.task_exceptions import TaskValidationError
from presentation.tui.commands.base import TUICommandBase
from presentation.tui.commands.decorators import handle_tui_errors
from presentation.tui.commands.registry import command_registry
from presentation.tui.forms.task_form_fields import TaskFormData
from presentation.tui.screens.task_form_dialog import TaskFormDialog


@command_registry.register("edit_task")
class EditTaskCommand(TUICommandBase):
    """Command to edit a task with input dialog."""

    def execute(self) -> None:  # noqa: C901
        """Execute the edit task command."""
        # Get selected task
        task = self.get_selected_task()
        if task is None:
            self.notify_warning("No task selected")
            return

        # Capture task fields for closure (should never be None for persisted tasks)
        if task.id is None:
            self.notify_error("Error editing task", Exception("Task ID is None"))
            return

        # Capture as concrete int type for closure
        task_id_value: int = task.id
        original_name = task.name
        original_priority = task.priority
        original_deadline = task.deadline
        original_estimated_duration = task.estimated_duration
        original_is_fixed = task.is_fixed
        original_depends_on = set(task.depends_on) if task.depends_on else set()

        @handle_tui_errors("editing task")
        def handle_task_data(form_data: TaskFormData | None) -> None:  # noqa: C901
            """Handle the task data from the dialog.

            Args:
                form_data: Form data or None if cancelled
            """
            if form_data is None:
                return  # User cancelled

            # Compare dependencies
            new_depends_on = set(form_data.depends_on) if form_data.depends_on else set()
            dependencies_changed = new_depends_on != original_depends_on

            # Check if anything changed
            if (
                form_data.name == original_name
                and form_data.priority == original_priority
                and form_data.deadline == original_deadline
                and form_data.estimated_duration == original_estimated_duration
                and form_data.is_fixed == original_is_fixed
                and not dependencies_changed
            ):
                self.notify_warning("No changes made")
                return

            # Use UseCase directly (UpdateTask has more complex logic)
            use_case = UpdateTaskUseCase(self.context.repository, self.context.time_tracker)
            task_input = UpdateTaskInput(
                task_id=task_id_value,
                name=form_data.name if form_data.name != original_name else None,
                priority=form_data.priority if form_data.priority != original_priority else None,
                deadline=form_data.deadline if form_data.deadline != original_deadline else None,
                estimated_duration=form_data.estimated_duration
                if form_data.estimated_duration != original_estimated_duration
                else None,
                is_fixed=form_data.is_fixed if form_data.is_fixed != original_is_fixed else None,
            )
            updated_task, updated_fields = use_case.execute(task_input)

            # Sync dependencies if changed
            if dependencies_changed:
                # Dependencies to remove (in original but not in new)
                deps_to_remove = original_depends_on - new_depends_on
                # Dependencies to add (in new but not in original)
                deps_to_add = new_depends_on - original_depends_on

                failed_operations = []

                # Remove dependencies
                if deps_to_remove:
                    remove_use_case = RemoveDependencyUseCase(self.context.repository)
                    for dep_id in deps_to_remove:
                        try:
                            remove_input = RemoveDependencyInput(
                                task_id=task_id_value, depends_on_id=dep_id
                            )
                            remove_use_case.execute(remove_input)
                        except TaskValidationError as e:
                            failed_operations.append(f"Remove {dep_id}: {e}")

                # Add dependencies
                if deps_to_add:
                    add_use_case = AddDependencyUseCase(self.context.repository)
                    for dep_id in deps_to_add:
                        try:
                            add_input = AddDependencyInput(
                                task_id=task_id_value, depends_on_id=dep_id
                            )
                            add_use_case.execute(add_input)
                        except TaskValidationError as e:
                            failed_operations.append(f"Add {dep_id}: {e}")

                # Add 'dependencies' to updated fields
                updated_fields.append("dependencies")

                # Show warnings for failed operations
                if failed_operations:
                    self.notify_warning(
                        "Some dependency operations failed:\n" + "\n".join(failed_operations)
                    )

            self.reload_tasks()

            if updated_fields:
                fields_str = ", ".join(updated_fields)
                self.notify_success(f"Updated task {updated_task.id}: {fields_str}")
            else:
                self.notify_warning("No changes made")

        # Show task form dialog in edit mode (with task parameter)
        dialog = TaskFormDialog(task=task, config=self.context.config)
        self.app.push_screen(dialog, handle_task_data)
