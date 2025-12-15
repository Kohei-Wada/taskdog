"""Task detail dialog for TUI."""

from typing import Any, ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, VerticalScroll
from textual.widgets import Label, Markdown, Static

from taskdog.constants.colors import STATUS_COLORS_BOLD
from taskdog.formatters.date_time_formatter import DateTimeFormatter
from taskdog.tui.dialogs.scrollable_dialog import ScrollableDialogBase
from taskdog_core.application.dto.task_detail_output import TaskDetailOutput
from taskdog_core.application.dto.task_dto import TaskDetailDto
from taskdog_core.shared.constants.formats import DATETIME_FORMAT


class TaskDetailDialog(ScrollableDialogBase[tuple[str, int] | None]):
    """Modal screen for displaying task details.

    Shows comprehensive information about a task including:
    - Basic info (ID, name, priority, status)
    - Schedule (planned start/end, deadline, estimated duration)
    - Actual tracking (actual start/end, actual duration)
    - Notes (if available)
    """

    BINDINGS: ClassVar = [
        *ScrollableDialogBase.BINDINGS,
        Binding("v", "note", "Edit Note", tooltip="Edit markdown notes for this task"),
    ]

    @property
    def scroll_container_id(self) -> str:
        """Return the ID of the scroll container."""
        return "#detail-content"

    def __init__(self, detail: TaskDetailOutput, *args: Any, **kwargs: Any):
        """Initialize the detail screen.

        Args:
            detail: TaskDetailOutput with task and notes
        """
        super().__init__(*args, **kwargs)
        if detail.task is None:
            raise ValueError("Task detail must not be None")
        self.task_data: TaskDetailDto = detail.task
        self.notes_content = detail.notes_content
        self.has_notes = detail.has_notes

    def compose(self) -> ComposeResult:
        """Compose the screen layout."""
        with Container(
            id="detail-screen", classes="dialog-base dialog-wide"
        ) as container:
            container.border_title = f"Task #{self.task_data.id}: {self.task_data.name}"

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
        status_color = STATUS_COLORS_BOLD.get(self.task_data.status.value, "white")
        status_styled = f"[{status_color}]{status_text}[/{status_color}]"
        yield Static(
            f"[dim]Status:[/dim] {status_styled}",
            classes="detail-row",
        )
        yield self._create_detail_row(
            "Created", DateTimeFormatter.format_created(self.task_data.created_at)
        )
        yield self._create_detail_row(
            "Updated", DateTimeFormatter.format_updated(self.task_data.updated_at)
        )

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
            yield from self._format_optional_datetime_row(
                "Planned Start", self.task_data.planned_start
            )
            yield from self._format_optional_datetime_row(
                "Planned End", self.task_data.planned_end
            )
            yield from self._format_optional_datetime_row(
                "Deadline", self.task_data.deadline
            )
            yield from self._format_optional_duration_row(
                "Estimated Duration", self.task_data.estimated_duration
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
            yield from self._format_optional_datetime_row(
                "Actual Start", self.task_data.actual_start
            )
            yield from self._format_optional_datetime_row(
                "Actual End", self.task_data.actual_end
            )
            yield from self._format_optional_duration_row(
                "Actual Duration", self.task_data.actual_duration_hours, precision=2
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

    def _format_optional_datetime_row(self, label: str, value: Any) -> ComposeResult:
        """Format an optional datetime field as a detail row.

        Args:
            label: Field label
            value: Optional datetime value

        Yields:
            Detail row widget if value exists
        """
        if value:
            yield self._create_detail_row(label, value.strftime(DATETIME_FORMAT))

    def _format_optional_duration_row(
        self, label: str, hours: float | None, precision: int = 0
    ) -> ComposeResult:
        """Format an optional duration field as a detail row.

        Args:
            label: Field label
            hours: Optional duration in hours
            precision: Decimal places for formatting (default: 0 for integers)

        Yields:
            Detail row widget if hours exists
        """
        if hours:
            formatted_hours = (
                f"{hours:.{precision}f}h" if precision > 0 else f"{hours}h"
            )
            yield self._create_detail_row(label, formatted_hours)

    def action_note(self) -> None:
        """Edit note (v key) - dismiss and return task ID to trigger note editing."""
        if self.task_data.id is None:
            return
        self.dismiss(("note", self.task_data.id))
