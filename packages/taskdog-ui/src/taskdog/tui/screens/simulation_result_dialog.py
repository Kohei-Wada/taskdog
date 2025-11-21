"""Dialog for displaying task simulation results."""

from typing import Any, ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, VerticalScroll
from textual.widgets import Label, Static

from taskdog.formatters.date_time_formatter import DateTimeFormatter
from taskdog.tui.screens.base_dialog import BaseModalDialog
from taskdog_core.application.dto.simulation_result import SimulationResult


class SimulationResultDialog(BaseModalDialog[None]):
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
            tooltip="Close the simulation results",
        ),
    ]

    def __init__(
        self,
        result: SimulationResult,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Initialize the dialog.

        Args:
            result: Simulation result to display
        """
        super().__init__(*args, **kwargs)
        self.result = result

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
        # Schedule section
        yield Static("[bold]Schedule:[/bold]")
        yield Static(
            f"  Planned Start: {DateTimeFormatter.format_datetime(result.planned_start)}"
        )
        yield Static(
            f"  Planned End: {DateTimeFormatter.format_datetime(result.planned_end)}"
        )
        if result.best_algorithm:
            yield Static(
                f"  Best Algorithm: [cyan]{result.best_algorithm}[/cyan] "
                f"({result.successful_algorithms}/{result.total_algorithms_tested} succeeded)"
            )
        yield Static("")

        # Task details section
        yield Static("[bold]Task Details:[/bold]")
        yield Static(f"  Name: {result.virtual_task_name}")
        yield Static(f"  Estimated: {result.estimated_duration} hours")
        yield Static(f"  Priority: {result.priority}")
        if result.deadline:
            yield Static(
                f"  Deadline: {DateTimeFormatter.format_datetime(result.deadline)}"
            )
        yield Static("")

        # Workload analysis section
        yield Static("[bold]Workload Analysis:[/bold]")
        if result.peak_date:
            yield Static(
                f"  Peak: {result.peak_workload:.1f}h on "
                f"{DateTimeFormatter.format_date_only(result.peak_date)}"
            )
        else:
            yield Static(f"  Peak: {result.peak_workload:.1f}h")
        yield Static(f"  Average: {result.average_workload:.1f}h/day")
        yield Static(f"  Total Days: {result.total_workload_days}")
        yield Static("")

        yield Static(
            "[dim]This is a simulation. Use 'taskdog add' to actually create the task.[/dim]"
        )

    def _compose_failure_result(self, result: SimulationResult) -> ComposeResult:
        """Compose failed simulation result.

        Args:
            result: Simulation result

        Yields:
            Result widgets
        """
        # Failure reason
        yield Static(
            f"[yellow]Reason:[/yellow] {result.failure_reason or 'Unknown error'}"
        )
        yield Static("")

        # Task details section
        yield Static("[bold]Task Details:[/bold]")
        yield Static(f"  Name: {result.virtual_task_name}")
        yield Static(f"  Estimated: {result.estimated_duration} hours")
        yield Static(f"  Priority: {result.priority}")
        if result.deadline:
            yield Static(
                f"  Deadline: {DateTimeFormatter.format_datetime(result.deadline)}"
            )
        yield Static("")

        # Algorithm testing info
        yield Static("[bold]Algorithm Testing:[/bold]")
        yield Static(f"  All {result.total_algorithms_tested} algorithms were tested")
        yield Static("  None could schedule this task with the given constraints")
        yield Static("")

        # Suggestions
        yield Static("[yellow]Suggestions:[/yellow]")
        yield Static("  • Adjust the deadline")
        yield Static("  • Increase max-hours-per-day")
        yield Static("  • Complete or cancel existing tasks to free up capacity")

    def action_close(self) -> None:
        """Close the dialog."""
        self.dismiss(None)
