"""Simulate task command for TUI."""

from typing import Any

from taskdog.tui.commands.base import TUICommandBase
from taskdog.tui.commands.registry import command_registry
from taskdog.tui.forms.task_form_fields import TaskFormData
from taskdog.tui.screens.simulate_task_dialog import (
    SimulateTaskDialog,
    SimulateTaskFormData,
)
from taskdog.tui.screens.simulation_result_dialog import SimulationResultDialog


@command_registry.register("simulate_task")
class SimulateTaskCommand(TUICommandBase):
    """Command to simulate a task without saving to database."""

    def execute(self) -> None:
        """Execute the simulate task command."""

        def handle_simulate_data(form_data: TaskFormData | None) -> None:
            """Handle the simulation data from the dialog.

            Args:
                form_data: Form data or None if cancelled
            """
            if form_data is None:
                return  # User cancelled

            # Type narrowing: we know this is actually SimulateTaskFormData
            assert isinstance(form_data, SimulateTaskFormData)

            try:
                # Run simulation via API client
                result = self.context.api_client.simulate_task(
                    estimated_duration=form_data.estimated_duration,
                    name=form_data.name,
                    priority=form_data.priority,
                    deadline=form_data.get_deadline(),
                    depends_on=form_data.depends_on,
                    tags=form_data.tags,
                    is_fixed=form_data.is_fixed,
                    max_hours_per_day=form_data.max_hours_per_day,
                )

                # Show simulation result dialog
                result_dialog = SimulationResultDialog(
                    result=result, form_data=form_data
                )
                self.app.push_screen(
                    result_dialog,
                    lambda should_create: self._handle_result_decision(
                        should_create, result, form_data
                    ),
                )

            except Exception as e:
                self.notify_error("Simulation failed", e)

        # Show simulate task form dialog
        # Wrap callback with error handling from base class
        dialog = SimulateTaskDialog(config=self.context.config)
        self.app.push_screen(dialog, self.handle_error(handle_simulate_data))

    def _handle_result_decision(
        self,
        should_create: bool | None,
        result: Any,
        form_data: SimulateTaskFormData,
    ) -> None:
        """Handle result dialog decision to create task.

        Args:
            should_create: True if user wants to create the task
            result: Simulation result
            form_data: Original form data
        """
        if not should_create:
            return  # User declined to create task

        # Only create task if simulation was successful
        if not result.is_schedulable:
            self.notify_error(
                "Cannot create task",
                Exception("Simulation failed - task cannot be scheduled"),
            )
            return

        # Verify planned dates are available
        if result.planned_start is None or result.planned_end is None:
            self.notify_error(
                "Cannot create task",
                Exception("Simulation result missing planned dates"),
            )
            return

        # Create the task
        try:
            task = self.context.api_client.create_task(
                name=form_data.name,
                priority=form_data.priority,
                deadline=form_data.get_deadline(),
                estimated_duration=form_data.estimated_duration,
                planned_start=result.planned_start,
                planned_end=result.planned_end,
                is_fixed=form_data.is_fixed,
                tags=form_data.tags or [],
            )

            # Add dependencies if specified
            if form_data.depends_on:
                for dep_id in form_data.depends_on:
                    self.context.api_client.add_dependency(task.id, dep_id)

            self.notify_success(f"Created task: {task.name} (ID: {task.id})")
            self.reload_tasks()
        except Exception as e:
            self.notify_error("Failed to create task", e)
