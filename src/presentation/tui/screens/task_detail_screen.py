"""Task detail screen for TUI."""

from typing import ClassVar

from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Label, Markdown, Static

from application.dto.task_detail_result import GetTaskDetailResult
from domain.entities.task import Task
from presentation.constants.colors import STATUS_COLORS_BOLD
from presentation.tui.screens.base_dialog import BaseModalDialog


class TaskDetailScreen(BaseModalDialog[tuple[str, int] | None]):
    """Modal screen for displaying task details.

    Shows comprehensive information about a task including:
    - Basic info (ID, name, priority, status)
    - Schedule (planned start/end, deadline, estimated duration)
    - Actual tracking (actual start/end, actual duration)
    - Notes (if available)
    """

    BINDINGS: ClassVar = [
        ("ctrl+d", "scroll_down", "Scroll Down"),
        ("ctrl+u", "scroll_up", "Scroll Up"),
        ("v", "edit_note", "Edit Note"),
    ]

    def __init__(self, detail: GetTaskDetailResult | Task, *args, **kwargs):
        """Initialize the detail screen.

        Args:
            detail: GetTaskDetailResult with task and notes, or Task object for backwards compatibility
        """
        super().__init__(*args, **kwargs)
        # Support both GetTaskDetailResult and Task for backwards compatibility
        if isinstance(detail, GetTaskDetailResult):
            self.task_data = detail.task
            self.notes_content = detail.notes_content
            self.has_notes = detail.has_notes
        else:
            self.task_data = detail
            self.notes_content = None
            self.has_notes = False

    def compose(self) -> ComposeResult:
        """Compose the screen layout."""
        with Container(id="detail-screen"):
            yield Label(
                f"[bold cyan]Task #{self.task_data.id}: {self.task_data.name}[/bold cyan]",
                id="dialog-title",
            )

            with VerticalScroll(id="detail-content"):
                # Notes Section (at the top if notes exist)
                if self.has_notes and self.notes_content:
                    yield from self._compose_notes_section()

                # Basic Information (compact)
                yield from self._compose_basic_info_section()

                # Schedule Information (compact)
                yield from self._compose_schedule_section()

                # Actual Tracking (compact)
                yield from self._compose_tracking_section()

    def _compose_notes_section(self) -> ComposeResult:
        """Compose the notes section."""
        yield Label("[bold cyan]Notes[/bold cyan]")
        yield Markdown(self.notes_content or "", classes="notes-content")
        yield Static("", classes="detail-row")  # Empty row for spacing

    def _compose_basic_info_section(self) -> ComposeResult:
        """Compose the basic task information section."""
        yield Label("[bold cyan]Task Information[/bold cyan]")
        yield self._create_detail_row("ID", str(self.task_data.id))
        yield self._create_detail_row("Priority", str(self.task_data.priority))

        # Format status with color
        status_text = self.task_data.status.value
        status_color = STATUS_COLORS_BOLD.get(self.task_data.status, "white")
        status_styled = f"[{status_color}]{status_text}[/{status_color}]"
        yield Static(
            f"[dim]Status:[/dim] {status_styled}",
            classes="detail-row",
        )
        yield self._create_detail_row("Created", str(self.task_data.timestamp))

        # Dependencies
        if self.task_data.depends_on:
            deps_str = ", ".join(str(dep_id) for dep_id in self.task_data.depends_on)
            yield self._create_detail_row("Dependencies", deps_str)
        else:
            yield self._create_detail_row("Dependencies", "-")

    def _compose_schedule_section(self) -> ComposeResult:
        """Compose the schedule information section."""
        if any(
            [
                self.task_data.planned_start,
                self.task_data.planned_end,
                self.task_data.deadline,
                self.task_data.estimated_duration,
            ]
        ):
            yield Static("", classes="detail-row")  # Empty row for spacing
            yield Label("[bold cyan]Schedule[/bold cyan]")
            if self.task_data.planned_start:
                yield self._create_detail_row("Planned Start", self.task_data.planned_start)
            if self.task_data.planned_end:
                yield self._create_detail_row("Planned End", self.task_data.planned_end)
            if self.task_data.deadline:
                yield self._create_detail_row("Deadline", self.task_data.deadline)
            if self.task_data.estimated_duration:
                yield self._create_detail_row(
                    "Estimated Duration", f"{self.task_data.estimated_duration}h"
                )

    def _compose_tracking_section(self) -> ComposeResult:
        """Compose the actual tracking section."""
        if any(
            [
                self.task_data.actual_start,
                self.task_data.actual_end,
                self.task_data.actual_duration_hours,
            ]
        ):
            yield Static("", classes="detail-row")  # Empty row for spacing
            yield Label("[bold cyan]Actual Tracking[/bold cyan]")
            if self.task_data.actual_start:
                yield self._create_detail_row("Actual Start", self.task_data.actual_start)
            if self.task_data.actual_end:
                yield self._create_detail_row("Actual End", self.task_data.actual_end)
            if self.task_data.actual_duration_hours:
                yield self._create_detail_row(
                    "Actual Duration", f"{self.task_data.actual_duration_hours:.2f}h"
                )

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

    def action_scroll_down(self) -> None:
        """Scroll down (Ctrl+D)."""
        scroll_widget = self.query_one("#detail-content", VerticalScroll)
        scroll_widget.scroll_relative(y=scroll_widget.size.height // 2, animate=False)

    def action_scroll_up(self) -> None:
        """Scroll up (Ctrl+U)."""
        scroll_widget = self.query_one("#detail-content", VerticalScroll)
        scroll_widget.scroll_relative(y=-(scroll_widget.size.height // 2), animate=False)

    def action_edit_note(self) -> None:
        """Edit note (v key) - dismiss and return task ID to trigger note editing."""
        if self.task_data.id is None:
            return
        self.dismiss(("edit_note", self.task_data.id))
