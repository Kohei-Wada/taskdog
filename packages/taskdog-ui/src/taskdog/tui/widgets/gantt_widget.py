"""Gantt chart widget for TUI.

This widget wraps the GanttDataTable and provides additional functionality
like date range management and automatic resizing.
"""

from datetime import date, timedelta
from typing import Any

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.events import Resize
from textual.widgets import Static

from taskdog.constants.gantt import (
    BORDER_WIDTH,
    CHARS_PER_DAY,
    DEFAULT_GANTT_WIDGET_WIDTH,
    MIN_CONSOLE_WIDTH,
    MIN_GANTT_DISPLAY_DAYS,
    MIN_TIMELINE_WIDTH,
)
from taskdog.renderers.gantt_cell_formatter import LEGEND_SPEC
from taskdog.tui.events import GanttPanRequested
from taskdog.tui.widgets.base_widget import TUIWidget
from taskdog.tui.widgets.gantt_data_table import GanttDataTable
from taskdog.view_models.gantt_view_model import GanttViewModel
from taskdog_core.shared.constants.time import DAYS_PER_WEEK


class GanttWidget(Vertical, TUIWidget):
    """A widget for displaying gantt chart using GanttDataTable.

    This widget manages the GanttDataTable and handles date range calculations
    based on available screen width.

    Layout:
    - Title (fixed at top, dock: top)
    - GanttDataTable (scrollable, height: 1fr)
    - Legend (fixed at bottom, dock: bottom)
    """

    # Allow maximize for this widget (same as TaskTable)
    allow_maximize = True

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the gantt widget."""
        super().__init__(*args, **kwargs)
        self.can_focus = False
        self._task_ids: list[int] = []
        self._pan_offset_days: int = 0  # Window shift through time (days from today)
        self._keep_scroll_position: bool = False  # Preserve scroll position on refresh
        self._gantt_table: GanttDataTable | None = None
        self._title_widget: Static | None = None
        self._legend_widget: Static | None = None

    def compose(self) -> ComposeResult:
        """Compose the widget layout.

        Returns:
            Iterable of widgets to display
        """
        # Title at top (fixed - not scrollable)
        self._title_widget = Static("", id="gantt-title")
        yield self._title_widget

        # GanttDataTable (scrollable via DataTable's built-in scroll)
        self._gantt_table = GanttDataTable(id="gantt-table")  # type: ignore[no-untyped-call]
        yield self._gantt_table

        # Legend at bottom (fixed - not scrollable)
        # Built as markup string so Textual resolves CSS variables like $primary.
        self._legend_widget = Static(self._build_legend_markup(), id="gantt-legend")
        yield self._legend_widget

    def update_gantt(
        self,
        task_ids: list[int],
        keep_scroll_position: bool = False,
    ) -> None:
        """Update the gantt chart with new data from TUIState.gantt_cache.

        The caller (TaskUIManager) must set TUIState.gantt_cache before calling this.
        This widget only reads from State and renders.

        Args:
            task_ids: List of task IDs (used to detect if data exists on resize)
            keep_scroll_position: Whether to preserve scroll position during refresh.
                                 Set to True for periodic updates to avoid scroll stuttering.
        """
        self._task_ids = task_ids
        self._keep_scroll_position = keep_scroll_position
        self._render_gantt()

    def _get_gantt_from_state(self) -> GanttViewModel | None:
        """Get gantt view model from app state with filter applied.

        Returns:
            Filtered GanttViewModel if gantt_filter_enabled and filter active,
            otherwise returns the full gantt_cache.
        """
        return self.tui_state.filtered_gantt

    def _render_gantt(self) -> None:
        """Render the gantt chart."""
        # Check if widget is mounted and table exists
        if not self.is_mounted or not self._gantt_table:
            return

        gantt_view_model = self._get_gantt_from_state()
        if not gantt_view_model:
            self._show_empty_message()
            return

        # Load gantt data (shows column headers even when empty, matching TaskTable behavior)
        self._load_gantt_data()

    def _display_table_message(self, column_label: str, message: str) -> None:
        """Display a single-column message in the gantt table.

        Helper method to consolidate the common pattern of showing messages
        in the gantt table (empty state, errors, general updates).

        Args:
            column_label: Label for the single column
            message: Message content to display
        """
        if not self._gantt_table:
            return
        self._gantt_table.clear(columns=True)
        self._gantt_table.reset_diff_state()
        # Add column with max width to fill the entire table
        from rich.text import Text

        self._gantt_table.add_column(Text(column_label, justify="center"))
        self._gantt_table.add_row(Text.from_markup(message, justify="center"))

    def update(self, message: str) -> None:
        """Update the gantt widget with a message.

        Args:
            message: Message to display
        """
        self._display_table_message("Message", message)

    def _show_empty_message(self) -> None:
        """Show empty message when no tasks are available."""
        self._display_table_message("Message", "[dim]No tasks to display[/dim]")

    def _load_gantt_data(self) -> None:
        """Load and display gantt data from the pre-computed gantt ViewModel."""
        try:
            gantt_view_model = self._get_gantt_from_state()
            if gantt_view_model and self._gantt_table:
                gantt_config = self.cli_config.gantt
                self._gantt_table.load_gantt(
                    gantt_view_model,
                    keep_scroll_position=self._keep_scroll_position,
                    comfortable_hours=gantt_config.workload_comfortable_hours,
                    moderate_hours=gantt_config.workload_moderate_hours,
                )
                self._update_title()
        except Exception as e:
            self._show_error_message(e)

    def _update_title(self) -> None:
        """Update title with date range, sort order, and filter status."""
        if not self._title_widget:
            return

        gantt_view_model = self._get_gantt_from_state()
        if not gantt_view_model:
            return

        start_date = gantt_view_model.start_date
        end_date = gantt_view_model.end_date
        # Access sort state from tui_state
        arrow = "↓" if self.tui_state.sort_reverse else "↑"

        # Build filter indicator (always shown)
        if self.tui_state.gantt_filter_enabled:
            filter_indicator = " [green]🔍 Filter: ON[/green]"
        else:
            filter_indicator = " [dim]🔍 Filter: OFF[/dim]"

        title_text = (
            f"[bold $primary]Gantt Chart[/bold $primary] "
            f"[dim]({start_date} to {end_date})[/dim] "
            f"[dim]- sorted by: {self.tui_state.sort_by} {arrow}[/dim]"
            f"{filter_indicator}"
        )
        self._title_widget.update(title_text)

    @staticmethod
    def _build_legend_markup() -> str:
        """Build the legend as a Textual markup string from the shared spec.

        Markup (not Rich Text) is used so Textual resolves CSS variables like
        ``$primary`` when the Static renders it. The accent segment defers its
        color to ``$primary``; the CLI renderer uses a literal color instead.
        """
        parts = []
        for seg in LEGEND_SPEC:
            style = f"{seg.style} $primary" if seg.accent else seg.style
            parts.append(f"[{style}]{seg.text}[/{style}]")
        return "".join(parts)

    def _show_error_message(self, error: Exception) -> None:
        """Show error message when rendering fails.

        Args:
            error: The exception that occurred
        """
        self._display_table_message(
            "Error", f"[red]Error rendering gantt: {error!s}[/red]"
        )
        if self._title_widget:
            self._title_widget.update("")
        if self._legend_widget:
            self._legend_widget.update("")

    def _calculate_display_days(self, widget_width: int | None = None) -> int:
        """Calculate optimal number of days to display.

        Args:
            widget_width: Widget width to use for calculation. If None, uses self.size.width.

        Returns:
            Number of days to display (rounded to weeks)
        """
        if widget_width is None:
            widget_width = self.size.width if self.size else DEFAULT_GANTT_WIDGET_WIDTH

        # Minimal overhead: just widget borders (2)
        # Table now takes full width without Center container
        console_width = max(widget_width - BORDER_WIDTH, MIN_CONSOLE_WIDTH)
        # Actual fixed columns width: ID(4) + Task(20) + Est(7) + spacing = ~31
        # Use even smaller value to allocate maximum space to timeline
        actual_fixed_width = 32
        timeline_width = max(console_width - actual_fixed_width, MIN_TIMELINE_WIDTH)
        max_days = timeline_width // CHARS_PER_DAY
        weeks = max(max_days // DAYS_PER_WEEK, 1)
        calculated_days = weeks * DAYS_PER_WEEK
        try:
            min_days: int = self.cli_config.gantt.min_display_days
        except (AttributeError, TypeError):
            min_days = MIN_GANTT_DISPLAY_DAYS
        return max(calculated_days, min_days)

    def _calculate_date_range_for_display(self, display_days: int) -> tuple[date, date]:
        """Calculate start and end dates based on display days.

        Always starts from the previous Monday and extends by the specified number of days.

        Args:
            display_days: Number of days to display

        Returns:
            Tuple of (start_date, end_date)
        """
        today = date.today()
        start_date = (
            today
            - timedelta(days=today.weekday())
            + timedelta(days=self._pan_offset_days)
        )
        end_date = start_date + timedelta(days=display_days - 1)
        return start_date, end_date

    def on_resize(self, event: Resize) -> None:
        """Handle resize events.

        Args:
            event: The resize event containing new size information
        """
        # Check if widget is mounted and has necessary data
        if not self.is_mounted:
            return
        gantt_view_model = self._get_gantt_from_state()
        if not (self._task_ids and gantt_view_model):
            return

        # Use size from event for accurate dimensions
        display_days = self._calculate_display_days(widget_width=event.size.width)
        self._recalculate_gantt_for_width(display_days)

    def _recalculate_gantt_for_width(self, display_days: int) -> None:
        """Recalculate gantt data for new screen width.

        Args:
            display_days: Number of days to display
        """
        start_date, end_date = self._calculate_date_range_for_display(display_days)

        # Only post resize event if date range actually changed
        # This prevents unnecessary API reloads when toggling visibility or other non-resize updates
        gantt_view_model = self._get_gantt_from_state()
        if (
            gantt_view_model
            and start_date == gantt_view_model.start_date
            and end_date == gantt_view_model.end_date
        ):
            return  # No change needed

        # Post event to request gantt recalculation from app
        # App has access to controllers and presenters
        # App's event handler will update the view model and trigger re-render
        from taskdog.tui.events import GanttResizeRequested

        self.post_message(GanttResizeRequested(display_days, start_date, end_date))

    def on_gantt_pan_requested(self, event: GanttPanRequested) -> None:
        """Shift the gantt window through time and refetch the new range.

        Keeps the window width constant (so render cost stays flat) and moves
        its anchor; the existing resize path re-fetches gantt data for the new
        date range.

        Args:
            event: Pan request carrying a week delta or a reset flag.
        """
        event.stop()
        if event.reset:
            if self._pan_offset_days == 0:
                return
            self._pan_offset_days = 0
        else:
            self._pan_offset_days += event.weeks * DAYS_PER_WEEK

        display_days = self._calculate_display_days()
        self._recalculate_gantt_for_width(display_days)

    def render_filtered_gantt(self) -> None:
        """Render gantt from TUIState.filtered_gantt.

        Called by MainScreen when filter state changes.
        """
        self._render_gantt()

    def update_title_only(self) -> None:
        """Update only the Gantt title without rebuilding the data table."""
        self._update_title()

    # Public API methods for external access

    def get_selected_task_id(self) -> int | None:
        """Get the task ID at the current Gantt cursor row.

        Returns:
            Task ID if cursor is on a task row, None otherwise.
        """
        if self._gantt_table:
            return self._gantt_table.get_selected_task_id()
        return None

    def get_sort_by(self) -> str:
        """Get current sort order.

        Returns:
            Current sort field (e.g., "deadline", "priority")
        """
        # Access sort state from tui_state (single source of truth)
        return self.tui_state.sort_by

    def update_view_model_and_render(self, keep_scroll_position: bool = False) -> None:
        """Re-render gantt from TUIState.gantt_cache.

        The caller (TaskUIManager) must update TUIState.gantt_cache before calling this.
        This widget only reads from State and renders.

        Args:
            keep_scroll_position: Whether to preserve scroll position during refresh.
                                 Set to True for periodic updates to avoid scroll stuttering.
        """
        self._keep_scroll_position = keep_scroll_position
        self.call_after_refresh(self._render_gantt)

    def calculate_date_range(
        self, widget_width: int | None = None
    ) -> tuple[date, date]:
        """Calculate date range for gantt display based on widget width.

        Convenience method that combines display day calculation and date range calculation.
        Always starts from the previous Monday and extends by the calculated number of days.

        Args:
            widget_width: Widget width to use for calculation. If None, uses self.size.width.

        Returns:
            Tuple of (start_date, end_date)
        """
        display_days = self._calculate_display_days(widget_width)
        return self._calculate_date_range_for_display(display_days)
