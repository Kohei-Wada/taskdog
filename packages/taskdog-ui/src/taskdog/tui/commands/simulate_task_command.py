"""Simulate task command for TUI."""

from taskdog.tui.commands.base import TUICommandBase
from taskdog.tui.commands.registry import command_registry
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

        def handle_simulate_data(form_data: SimulateTaskFormData | None) -> None:
            """Handle the simulation data from the dialog.

            Args:
                form_data: Form data or None if cancelled
            """
            if form_data is None:
                return  # User cancelled

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

                # Show simulation result in a new dialog
                def handle_result_close(_: None) -> None:
                    """Handle result dialog close."""
                    pass

                result_dialog = SimulationResultDialog(result=result)
                self.app.push_screen(result_dialog, handle_result_close)

            except Exception as e:
                self.notify_error("Simulation failed", e)

        # Show simulate task form dialog
        # Wrap callback with error handling from base class
        dialog = SimulateTaskDialog(config=self.context.config)
        self.app.push_screen(dialog, self.handle_error(handle_simulate_data))
