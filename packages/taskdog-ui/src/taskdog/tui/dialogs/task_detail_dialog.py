"""Task detail dialog for TUI."""

import asyncio
from typing import Any, ClassVar

from taskdog_client.taskdog_api_client import TaskdogApiClient
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, VerticalScroll
from textual.css.query import NoMatches
from textual.widgets import Label, Markdown, Static, TabbedContent, TabPane, Tabs

from taskdog.constants.colors import STATUS_COLORS_BOLD
from taskdog.formatters.date_time_formatter import DateTimeFormatter
from taskdog.tui.dialogs.base_dialog import BaseModalDialog
from taskdog.tui.widgets.audit_log_entry_builder import create_audit_entry_widget
from taskdog.tui.widgets.vi_navigation_mixin import ViNavigationMixin
from taskdog_core.application.dto.task_detail_output import TaskDetailOutput
from taskdog_core.application.dto.task_dto import TaskDetailDto
from taskdog_core.shared.constants.formats import DATETIME_FORMAT

# Mapping from tab pane ID to its VerticalScroll child ID
_TAB_SCROLL_MAP: dict[str, str] = {
    "tab-detail": "detail-tab-scroll",
    "tab-notes": "notes-tab-scroll",
    "tab-audit": "audit-tab-scroll",
}


class TaskDetailDialog(BaseModalDialog[tuple[str, int] | None], ViNavigationMixin):
    """Modal screen for displaying task details with tabs.

    Shows comprehensive information about a task across three tabs:
    - Notes: Markdown notes
    - Detail: Basic info (ID, name, priority, status), schedule, tracking
    - Audit Log: Task-specific operation history (lazy-loaded)
    """

    BINDINGS: ClassVar = [
        *ViNavigationMixin.VI_VERTICAL_BINDINGS,
        *ViNavigationMixin.VI_PAGE_BINDINGS,
        Binding("q", "cancel", "Close", tooltip="Close the dialog"),
        Binding("v", "note", "Edit Note", tooltip="Edit markdown notes for this task"),
        Binding(
            "greater_than_sign",
            "next_tab",
            "Next Tab",
            show=False,
            priority=True,
            tooltip="Switch to next tab",
        ),
        Binding(
            "less_than_sign",
            "prev_tab",
            "Prev Tab",
            show=False,
            priority=True,
            tooltip="Switch to previous tab",
        ),
    ]

    def __init__(
        self,
        detail: TaskDetailOutput,
        *args: Any,
        api_client: TaskdogApiClient | None = None,
        **kwargs: Any,
    ):
        """Initialize the detail screen.

        Args:
            detail: TaskDetailOutput with task and notes
            api_client: Optional API client for fetching audit logs
        """
        super().__init__(*args, **kwargs)
        if detail.task is None:
            raise ValueError("Task detail must not be None")
        self.task_data: TaskDetailDto = detail.task
        self.notes_content = detail.notes_content
        self.has_notes = detail.has_notes
        self._api_client = api_client
        self._audit_loaded = False

    def compose(self) -> ComposeResult:
        """Compose the screen layout."""
        with Container(
            id="detail-screen", classes="dialog-base dialog-wide"
        ) as container:
            container.border_title = f"Task #{self.task_data.id}: {self.task_data.name}"

            with TabbedContent(id="detail-tabs"):
                with (
                    TabPane("Notes", id="tab-notes"),
                    VerticalScroll(id="notes-tab-scroll", classes="detail-tab-scroll"),
                ):
                    yield from self._compose_notes_tab()

                with (
                    TabPane("Detail", id="tab-detail"),
                    VerticalScroll(id="detail-tab-scroll", classes="detail-tab-scroll"),
                ):
                    yield from self._compose_basic_info_section()
                    yield from self._compose_schedule_section()
                    yield from self._compose_tracking_section()

                with (
                    TabPane("Audit Log", id="tab-audit"),
                    VerticalScroll(id="audit-tab-scroll", classes="detail-tab-scroll"),
                ):
                    yield Static(
                        "[dim]Select this tab to load audit logs...[/dim]",
                        id="audit-placeholder",
                    )

    def _compose_notes_tab(self) -> ComposeResult:
        """Compose the notes tab content."""
        if self.has_notes and self.notes_content:
            yield Markdown(self.notes_content, classes="notes-content")
        else:
            yield Static(
                "[dim]No notes. Press [bold]v[/bold] to add notes.[/dim]",
                classes="detail-row",
            )

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

    # ── Vi navigation (delegates to active tab's scroll widget) ──────────

    def _get_active_scroll_widget(self) -> VerticalScroll | None:
        """Get the VerticalScroll widget for the currently active tab.

        Returns:
            The active tab's VerticalScroll, or None if not found.
        """
        try:
            tabs = self.query_one("#detail-tabs", TabbedContent)
        except NoMatches:
            return None

        active_pane = tabs.active
        scroll_id = _TAB_SCROLL_MAP.get(active_pane, "")
        if not scroll_id:
            return None

        try:
            return self.query_one(f"#{scroll_id}", VerticalScroll)
        except NoMatches:
            return None

    def action_vi_down(self) -> None:
        """Scroll down one line (j key)."""
        widget = self._get_active_scroll_widget()
        if widget:
            widget.scroll_relative(y=1, animate=False)

    def action_vi_up(self) -> None:
        """Scroll up one line (k key)."""
        widget = self._get_active_scroll_widget()
        if widget:
            widget.scroll_relative(y=-1, animate=False)

    def action_vi_page_down(self) -> None:
        """Scroll down half page (Ctrl+D)."""
        widget = self._get_active_scroll_widget()
        if widget:
            widget.scroll_relative(y=widget.size.height // 2, animate=False)

    def action_vi_page_up(self) -> None:
        """Scroll up half page (Ctrl+U)."""
        widget = self._get_active_scroll_widget()
        if widget:
            widget.scroll_relative(y=-(widget.size.height // 2), animate=False)

    def action_vi_home(self) -> None:
        """Scroll to top (g key)."""
        widget = self._get_active_scroll_widget()
        if widget:
            widget.scroll_home(animate=False)

    def action_vi_end(self) -> None:
        """Scroll to bottom (G key)."""
        widget = self._get_active_scroll_widget()
        if widget:
            widget.scroll_end(animate=False)

    # ── Tab switching ──────────────────────────────────────────────────

    def action_next_tab(self) -> None:
        """Switch to the next tab (> key)."""
        try:
            tabs = self.query_one("#detail-tabs", TabbedContent).query_one(Tabs)
            tabs.action_next_tab()
        except NoMatches:
            pass

    def action_prev_tab(self) -> None:
        """Switch to the previous tab (< key)."""
        try:
            tabs = self.query_one("#detail-tabs", TabbedContent).query_one(Tabs)
            tabs.action_previous_tab()
        except NoMatches:
            pass

    # ── Audit log lazy loading ───────────────────────────────────────────

    def on_tabbed_content_tab_activated(
        self, event: TabbedContent.TabActivated
    ) -> None:
        """Handle tab activation to lazy-load audit logs."""
        pane = event.tabbed_content.active
        if pane == "tab-audit" and not self._audit_loaded:
            self._audit_loaded = True
            self._load_audit_logs()

    def _load_audit_logs(self) -> None:
        """Start loading audit logs in a background worker."""
        if self._api_client is None or self.task_data.id is None:
            self._show_audit_error("API client not available")
            return
        self.app.run_worker(self._fetch_audit_logs(), exclusive=True)

    async def _fetch_audit_logs(self) -> None:
        """Fetch audit logs from the API in a background thread."""
        try:
            result = await asyncio.to_thread(
                self._api_client.list_audit_logs,  # type: ignore[union-attr]
                resource_id=self.task_data.id,
                resource_type="task",
                limit=50,
            )
        except Exception:
            self._show_audit_error("Failed to load audit logs")
            return

        # Remove placeholder and mount log entries
        try:
            placeholder = self.query_one("#audit-placeholder", Static)
            placeholder.remove()
        except NoMatches:
            pass

        try:
            scroll = self.query_one("#audit-tab-scroll", VerticalScroll)
        except NoMatches:
            return

        if not result.logs:
            scroll.mount(
                Static(
                    "[dim]No audit logs for this task.[/dim]",
                    classes="detail-row",
                )
            )
            return

        for log in result.logs:
            entry = create_audit_entry_widget(log)
            scroll.mount(entry)

    def _show_audit_error(self, message: str) -> None:
        """Show an error message in the audit tab."""
        try:
            placeholder = self.query_one("#audit-placeholder", Static)
            placeholder.update(f"[dim]{message}[/dim]")
        except NoMatches:
            pass

    # ── Actions ──────────────────────────────────────────────────────────

    def action_note(self) -> None:
        """Edit note (v key) - dismiss and return task ID to trigger note editing."""
        if self.task_data.id is None:
            return
        self.dismiss(("note", self.task_data.id))
