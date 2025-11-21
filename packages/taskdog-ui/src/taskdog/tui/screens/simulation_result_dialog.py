"""Dialog for displaying task simulation results."""

from typing import Any, ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Button, Label, Static

from taskdog.formatters.date_time_formatter import DateTimeFormatter
from taskdog.tui.screens.base_dialog import BaseModalDialog
from taskdog.tui.screens.simulate_task_dialog import SimulateTaskFormData
from taskdog_core.application.dto.simulation_result import SimulationResult


class SimulationResultDialog(BaseModalDialog[bool]):
    """Modal dialog for displaying simulation results.

    Shows whether a task can be scheduled and when it would be completed,
    along with workload analysis and algorithm selection information.
    """

    BINDINGS: ClassVar = [
        Binding(
            "escape",
            "close",
            "Close",
            tooltip="Close the simulation results",
        ),
        Binding(
            "enter",
            "close",
            "Close",
            tooltip="Close without creating task",
        ),
        Binding("y", "create", "Yes", tooltip="Create the task"),
        Binding("n", "close", "No", tooltip="Close without creating task"),
    ]

    def __init__(
        self,
        result: SimulationResult,
        form_data: SimulateTaskFormData,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Initialize the dialog.

        Args:
            result: Simulation result to display
            form_data: Original form data used for simulation
        """
        super().__init__(*args, **kwargs)
        self.result = result
        self.form_data = form_data

    def compose(self) -> ComposeResult:
        """Compose the dialog layout."""
        result = self.result

        # Determine title and style based on schedulability
        if result.is_schedulable:
            title = "✓ Task Can Be Scheduled"
            title_class = "success-title"
        else:
            title = "✗ Task Cannot Be Scheduled"
            title_class = "error-title"

        with Container(
            id="simulation-result-dialog", classes="dialog-base dialog-wide"
        ) as container:
            container.border_title = "Simulation Result"

            # Show different hints based on success/failure
            if result.is_schedulable:
                yield Label(
                    "[dim]Y: create task | N/Enter/Escape: close[/dim]",
                    id="dialog-hint",
                )
            else:
                yield Label(
                    "[dim]Enter/Escape: close[/dim]",
                    id="dialog-hint",
                )

            with VerticalScroll():
                # Title
                yield Static(title, classes=title_class)
                yield Static("")

                if result.is_schedulable:
                    yield from self._compose_success_result(result)
                else:
                    yield from self._compose_failure_result(result)

    def _compose_success_result(self, result: SimulationResult) -> ComposeResult:
        """Compose successful simulation result.

        Args:
            result: Simulation result

        Yields:
            Result widgets
        """
        # Task name
        yield Static(f"[bold]Task:[/bold] {result.virtual_task_name}")
        yield Static("")

        # Prominent schedule display
        yield Static(
            f"[bold green]Start:[/bold green] [green]{DateTimeFormatter.format_datetime(result.planned_start)}[/green]"
        )
        yield Static(
            f"[bold cyan]End:[/bold cyan]   [cyan]{DateTimeFormatter.format_datetime(result.planned_end)}[/cyan]"
        )
        yield Static("")

        # Summary info
        yield Static(
            f"Duration: {result.estimated_duration}h  |  "
            f"Days: {result.total_workload_days}  |  "
            f"Avg: {result.average_workload:.1f}h/day"
        )
        yield Static("")

        yield Static("[bold]Create this task?[/bold]")
        with Horizontal(id="button-container"):
            yield Button("Yes (y)", variant="primary", id="yes-button")
            yield Button("No (n)", variant="default", id="no-button")

    def _compose_failure_result(self, result: SimulationResult) -> ComposeResult:
        """Compose failed simulation result.

        Args:
            result: Simulation result

        Yields:
            Result widgets
        """
        # Task name
        yield Static(f"[bold]Task:[/bold] {result.virtual_task_name}")
        yield Static("")

        # Failure reason
        yield Static(
            f"[bold red]Reason:[/bold red] {result.failure_reason or 'Unknown error'}"
        )
        yield Static("")

        # Suggestions
        yield Static("[bold yellow]Try:[/bold yellow]")
        yield Static("  • Adjust the deadline")
        yield Static("  • Increase max-hours-per-day")
        yield Static("  • Complete existing tasks")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "yes-button":
            self.dismiss(True)
        elif event.button.id == "no-button":
            self.dismiss(False)

    def action_create(self) -> None:
        """Create the task (y key)."""
        if self.result.is_schedulable:
            self.dismiss(True)

    def action_close(self) -> None:
        """Close the dialog without creating task."""
        self.dismiss(False)
