"""Gantt chart widget for TUI.

This widget wraps the GanttDataTable and provides additional functionality
like date range management and automatic resizing.
"""

from datetime import date, timedelta
from typing import Any

from textual.app import ComposeResult
from textual.containers import Center, VerticalScroll
from textual.events import Resize
from textual.widgets import Static

from taskdog.constants.table_dimensions import (
    BORDER_WIDTH,
    CHARS_PER_DAY,
    DEFAULT_GANTT_WIDGET_WIDTH,
    GANTT_TABLE_FIXED_WIDTH,
    MIN_CONSOLE_WIDTH,
    MIN_TIMELINE_WIDTH,
)
from taskdog.tui.widgets.gantt_data_table import GanttDataTable
from taskdog.view_models.gantt_view_model import GanttViewModel
from taskdog_core.application.queries.filters.task_filter import TaskFilter
from taskdog_core.shared.constants.time import DAYS_PER_WEEK
from taskdog_core.shared.utils.date_utils import get_previous_monday


class GanttWidget(VerticalScroll):
    """A widget for displaying gantt chart using GanttDataTable.

    This widget manages the GanttDataTable and handles date range calculations
    based on available screen width.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the gantt widget."""
        super().__init__(*args, **kwargs)
        self._task_ids: list[int] = []
        self._gantt_view_model: GanttViewModel | None = None
        self._sort_by: str = "deadline"  # Default sort order
        self._task_filter: TaskFilter | None = None  # Filter for recalculation
        self._gantt_table: GanttDataTable | None = None
        self._title_widget: Static | None = None
        self._legend_widget: Static | None = None

    def compose(self) -> ComposeResult:
        """Compose the widget layout.

        Returns:
            Iterable of widgets to display
        """
        # Title above the table
        self._title_widget = Static("")
        self._title_widget.styles.text_align = "center"
        self._title_widget.styles.margin = (0, 0, 1, 0)  # Bottom margin
        yield self._title_widget

        # Create GanttDataTable
        self._gantt_table = GanttDataTable(id="gantt-table")
        self._gantt_table.styles.width = "auto"

        # Wrap table in Center container for horizontal centering
        with Center():
            yield self._gantt_table

        # Legend below the table
        self._legend_widget = Static("")
        self._legend_widget.styles.text_align = "center"
        self._legend_widget.styles.margin = (1, 0, 0, 0)  # Top margin
        yield self._legend_widget

    def update_gantt(
        self,
        task_ids: list[int],
        gantt_view_model: GanttViewModel,
        sort_by: str = "deadline",
        task_filter: TaskFilter | None = None,
    ):
        """Update the gantt chart with new gantt data.

        Args:
            task_ids: List of task IDs (used for recalculating date range on resize)
            gantt_view_model: Presentation-ready gantt data
            sort_by: Sort order for tasks (default: "deadline")
            task_filter: Filter object to use for recalculation on resize (optional)
        """
        self._task_ids = task_ids
        self._gantt_view_model = gantt_view_model
        self._sort_by = sort_by
        if task_filter is not None:
            self._task_filter = task_filter
        self._render_gantt()

    def _render_gantt(self):
        """Render the gantt chart."""
        # Check if widget is mounted and table exists
        if not self.is_mounted or not self._gantt_table:
            return

        if not self._gantt_view_model or self._gantt_view_model.is_empty():
            self._show_empty_message()
            return

        # Directly load the pre-computed gantt data
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
        self._gantt_table.add_column(column_label)
        self._gantt_table.add_row(message)

    def update(self, message: str) -> None:
        """Update the gantt widget with a message.

        Args:
            message: Message to display
        """
        self._display_table_message("Message", message)

    def _show_empty_message(self):
        """Show empty message when no tasks are available."""
        self._display_table_message("Message", "[dim]No tasks to display[/dim]")

    def _load_gantt_data(self):
        """Load and display gantt data from the pre-computed gantt ViewModel."""
        try:
            self._gantt_table.load_gantt(self._gantt_view_model)
            self._update_title()
            self._update_legend()
        except Exception as e:
            self._show_error_message(e)

    def _update_title(self):
        """Update title with date range and sort order."""
        if not self._title_widget:
            return

        start_date = self._gantt_view_model.start_date
        end_date = self._gantt_view_model.end_date
        title_text = (
            f"[bold yellow]Gantt Chart[/bold yellow] "
            f"[dim]({start_date} to {end_date})[/dim] "
            f"[dim]- sorted by: {self._sort_by}[/dim]"
        )
        self._title_widget.update(title_text)

    def _update_legend(self):
        """Update legend with gantt chart symbols."""
        if not self._legend_widget:
            return

        legend_text = self._gantt_table.get_legend_text()
        self._legend_widget.update(legend_text)

    def _show_error_message(self, error: Exception):
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
        console_width = max(widget_width - BORDER_WIDTH, MIN_CONSOLE_WIDTH)
        timeline_width = max(
            console_width - GANTT_TABLE_FIXED_WIDTH, MIN_TIMELINE_WIDTH
        )
        max_days = timeline_width // CHARS_PER_DAY
        weeks = max(max_days // DAYS_PER_WEEK, 1)
        return weeks * DAYS_PER_WEEK

    def _calculate_date_range_for_display(self, display_days: int) -> tuple[date, date]:
        """Calculate start and end dates based on display days.

        Always starts from the previous Monday and extends by the specified number of days.

        Args:
            display_days: Number of days to display

        Returns:
            Tuple of (start_date, end_date)
        """
        start_date = get_previous_monday()
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
        if not (self._task_ids and self._gantt_view_model):
            return

        # Use size from event for accurate dimensions
        display_days = self._calculate_display_days(widget_width=event.size.width)
        self._recalculate_gantt_for_width(display_days)

    def _recalculate_gantt_for_width(self, display_days: int):
        """Recalculate gantt data for new screen width.

        Args:
            display_days: Number of days to display
        """
        start_date, end_date = self._calculate_date_range_for_display(display_days)

        # Only post resize event if date range actually changed
        # This prevents unnecessary API reloads when toggling visibility or other non-resize updates
        if (
            self._gantt_view_model
            and start_date == self._gantt_view_model.start_date
            and end_date == self._gantt_view_model.end_date
        ):
            return  # No change needed

        # Post event to request gantt recalculation from app
        # App has access to controllers and presenters
        # App's event handler will update the view model and trigger re-render
        from taskdog.tui.events import GanttResizeRequested

        self.post_message(GanttResizeRequested(display_days, start_date, end_date))

    # Public API methods for external access

    def get_task_filter(self):
        """Get current task filter.

        Returns:
            Current TaskFilter object or None
        """
        return self._task_filter

    def get_sort_by(self) -> str:
        """Get current sort order.

        Returns:
            Current sort field (e.g., "deadline", "priority")
        """
        return self._sort_by

    def update_view_model_and_render(self, gantt_view_model) -> None:
        """Update gantt view model and trigger re-render.

        This method updates the internal view model and schedules a re-render
        after the next refresh cycle.

        Args:
            gantt_view_model: New GanttViewModel to display
        """
        self._gantt_view_model = gantt_view_model
        self.call_after_refresh(self._render_gantt)

    def calculate_display_days(self, widget_width: int | None = None) -> int:
        """Calculate optimal number of days to display based on widget width.

        Public interface for display day calculation. This is useful for
        determining date ranges before loading gantt data.

        Args:
            widget_width: Widget width to use for calculation. If None, uses self.size.width.

        Returns:
            Number of days to display (rounded to weeks)
        """
        return self._calculate_display_days(widget_width)

    def calculate_date_range(self, widget_width: int | None = None):
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
