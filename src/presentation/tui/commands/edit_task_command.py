"""Edit task command for TUI."""

from dataclasses import dataclass

from application.dto.update_task_request import UpdateTaskRequest
from application.use_cases.update_task import UpdateTaskUseCase
from domain.entities.task import Task
from domain.exceptions.task_exceptions import TaskValidationError
from presentation.tui.commands.base import TUICommandBase
from presentation.tui.commands.registry import command_registry
from presentation.tui.forms.task_form_fields import TaskFormData
from presentation.tui.helpers.dependency_helpers import sync_dependencies
from presentation.tui.screens.task_form_dialog import TaskFormDialog


@dataclass
class OriginalTaskValues:
    """Captured original task values for change detection."""

    task_id: int
    name: str
    priority: int
    deadline: str | None
    estimated_duration: float | None
    planned_start: str | None
    planned_end: str | None
    is_fixed: bool
    depends_on: set[int]


@command_registry.register("edit_task")
class EditTaskCommand(TUICommandBase):
    """Command to edit a task with input dialog."""

    def execute(self) -> None:
        """Execute the edit task command."""
        # Get selected task
        task = self.get_selected_task()
        if task is None:
            self.notify_warning("No task selected")
            return

        if task.id is None:
            self.notify_error("Error editing task", Exception("Task ID is None"))
            return

        # Capture original values
        original = self._capture_original_values(task)

        def handle_task_data(form_data: TaskFormData | None) -> None:
            """Handle the task data from the dialog."""
            if form_data is None:
                return  # User cancelled

            try:
                self._handle_task_update(original, form_data)
            except TaskValidationError as e:
                self.notify_error("Validation error", e)
            except Exception as e:
                self.notify_error("Error editing task", e)

        # Show task form dialog in edit mode
        dialog = TaskFormDialog(task=task, config=self.context.config)
        self.app.push_screen(dialog, handle_task_data)

    def _capture_original_values(self, task: Task) -> OriginalTaskValues:
        """Capture original task values for change detection.

        Args:
            task: Task to capture values from

        Returns:
            OriginalTaskValues with all fields captured
        """
        return OriginalTaskValues(
            task_id=task.id,  # type: ignore
            name=task.name,
            priority=task.priority,
            deadline=task.deadline,
            estimated_duration=task.estimated_duration,
            planned_start=task.planned_start,
            planned_end=task.planned_end,
            is_fixed=task.is_fixed,
            depends_on=set(task.depends_on) if task.depends_on else set(),
        )

    def _detect_changes(
        self, original: OriginalTaskValues, form_data: TaskFormData
    ) -> tuple[bool, bool]:
        """Detect what changed between original and form data.

        Args:
            original: Original task values
            form_data: New form data

        Returns:
            Tuple of (has_field_changes, has_dependency_changes)
        """
        new_depends_on = set(form_data.depends_on) if form_data.depends_on else set()
        dependencies_changed = new_depends_on != original.depends_on

        fields_changed = (
            form_data.name != original.name
            or form_data.priority != original.priority
            or form_data.deadline != original.deadline
            or form_data.estimated_duration != original.estimated_duration
            or form_data.planned_start != original.planned_start
            or form_data.planned_end != original.planned_end
            or form_data.is_fixed != original.is_fixed
        )

        return fields_changed, dependencies_changed

    def _build_update_input(
        self, original: OriginalTaskValues, form_data: TaskFormData
    ) -> UpdateTaskRequest:
        """Build UpdateTaskRequest with only changed fields.

        Args:
            original: Original task values
            form_data: New form data

        Returns:
            UpdateTaskRequest with only changed fields set
        """
        return UpdateTaskRequest(
            task_id=original.task_id,
            name=form_data.name if form_data.name != original.name else None,
            priority=form_data.priority if form_data.priority != original.priority else None,
            deadline=form_data.deadline if form_data.deadline != original.deadline else None,
            estimated_duration=form_data.estimated_duration
            if form_data.estimated_duration != original.estimated_duration
            else None,
            planned_start=form_data.planned_start
            if form_data.planned_start != original.planned_start
            else None,
            planned_end=form_data.planned_end
            if form_data.planned_end != original.planned_end
            else None,
            is_fixed=form_data.is_fixed if form_data.is_fixed != original.is_fixed else None,
        )

    def _sync_dependencies_and_notify(
        self, original: OriginalTaskValues, form_data: TaskFormData, updated_fields: list[str]
    ) -> None:
        """Synchronize dependencies and notify on failures.

        Args:
            original: Original task values
            form_data: New form data
            updated_fields: List to append 'dependencies' to if changed
        """
        new_depends_on = set(form_data.depends_on) if form_data.depends_on else set()
        failed_operations = sync_dependencies(
            original.task_id, original.depends_on, new_depends_on, self.context.repository
        )

        updated_fields.append("dependencies")

        if failed_operations:
            self.notify_warning(
                "Some dependency operations failed:\n" + "\n".join(failed_operations)
            )

    def _handle_task_update(self, original: OriginalTaskValues, form_data: TaskFormData) -> None:
        """Handle the actual task update logic.

        Args:
            original: Original task values
            form_data: New form data from dialog
        """
        # Detect changes
        fields_changed, dependencies_changed = self._detect_changes(original, form_data)

        # Check if anything changed
        if not fields_changed and not dependencies_changed:
            self.notify_warning("No changes made")
            return

        # Update task fields
        use_case = UpdateTaskUseCase(self.context.repository, self.context.time_tracker)
        task_input = self._build_update_input(original, form_data)
        updated_task, updated_fields = use_case.execute(task_input)

        # Sync dependencies if changed
        if dependencies_changed:
            self._sync_dependencies_and_notify(original, form_data, updated_fields)

        self.reload_tasks()

        if updated_fields:
            fields_str = ", ".join(updated_fields)
            self.notify_success(f"Updated task {updated_task.id}: {fields_str}")
        else:
            self.notify_warning("No changes made")
