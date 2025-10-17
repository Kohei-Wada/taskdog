"""Task detail screen for TUI."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Button, Label, Static

from domain.entities.task import Task
from presentation.constants.colors import STATUS_COLORS_BOLD
from presentation.tui.screens.base_dialog import BaseModalDialog


class TaskDetailScreen(BaseModalDialog[None]):
    """Modal screen for displaying task details.

    Shows comprehensive information about a task including:
    - Basic info (ID, name, priority, status)
    - Schedule (planned start/end, deadline, estimated duration)
    - Actual tracking (actual start/end, actual duration)
    """

    def __init__(self, task: Task, *args, **kwargs):
        """Initialize the detail screen.

        Args:
            task: The task to display
        """
        super().__init__(*args, **kwargs)
        self.task_data = task

    def compose(self) -> ComposeResult:
        """Compose the screen layout."""
        with Container(id="detail-screen"):
            yield Label("[bold cyan]Task Details[/bold cyan]", id="dialog-title")

            with VerticalScroll(id="detail-content"):
                # Basic Information
                yield Label("[bold yellow]Basic Information[/bold yellow]")
                yield self._create_detail_row("ID", str(self.task_data.id))
                yield self._create_detail_row("Name", self.task_data.name)
                yield self._create_detail_row("Priority", str(self.task_data.priority))

                # Format status with color
                status_text = self.task_data.status.value
                status_color = STATUS_COLORS_BOLD.get(self.task_data.status, "white")
                status_styled = f"[{status_color}]{status_text}[/{status_color}]"
                yield Static(
                    f"[dim]Status:[/dim] {status_styled}",
                    classes="detail-row",
                )

                # Schedule Information
                yield Static("", classes="detail-row")  # Empty row for spacing
                yield Label("[bold yellow]Schedule[/bold yellow]")
                yield self._create_detail_row(
                    "Planned Start", self.task_data.planned_start or "Not set"
                )
                yield self._create_detail_row(
                    "Planned End", self.task_data.planned_end or "Not set"
                )
                yield self._create_detail_row("Deadline", self.task_data.deadline or "Not set")
                yield self._create_detail_row(
                    "Estimated Duration",
                    f"{self.task_data.estimated_duration}h"
                    if self.task_data.estimated_duration
                    else "Not set",
                )

                # Actual Tracking
                yield Static("", classes="detail-row")  # Empty row for spacing
                yield Label("[bold yellow]Actual Tracking[/bold yellow]")
                yield self._create_detail_row(
                    "Actual Start", self.task_data.actual_start or "Not started"
                )
                yield self._create_detail_row(
                    "Actual End", self.task_data.actual_end or "Not finished"
                )
                yield self._create_detail_row(
                    "Actual Duration",
                    f"{self.task_data.actual_duration_hours:.2f}h"
                    if self.task_data.actual_duration_hours
                    else "N/A",
                )

                # Additional Info
                yield Static("", classes="detail-row")  # Empty row for spacing
                yield Label("[bold yellow]Additional Info[/bold yellow]")
                yield self._create_detail_row("Created", str(self.task_data.timestamp))
                yield self._create_detail_row(
                    "Notes",
                    f"{self.task_data.notes_path}" if self.task_data.notes_path else "No notes",
                )

            with Horizontal(id="button-container"):
                yield Button("Close (Esc)", variant="default", id="close-button")

    def _create_detail_row(self, label: str, value: str) -> Static:
        """Create a detail row with label and value.

        Args:
            label: Field label
            value: Field value

        Returns:
            Static widget with formatted row
        """
        return Static(
            f"[dim]{label}:[/dim] {value}",
            classes="detail-row",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "close-button":
            self.dismiss(None)
