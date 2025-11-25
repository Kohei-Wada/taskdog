"""Gantt chart widget for TUI.

This widget wraps the GanttDataTable and provides additional functionality
like date range management and automatic resizing.
"""

from datetime import date, timedelta
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    pass

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.events import Resize
from textual.widgets import Static

from taskdog.constants.table_dimensions import (
    BORDER_WIDTH,
    CHARS_PER_DAY,
    DEFAULT_GANTT_WIDGET_WIDTH,
    MIN_CONSOLE_WIDTH,
    MIN_TIMELINE_WIDTH,
)
from taskdog.tui.widgets.base_widget import TUIWidget
from taskdog.tui.widgets.gantt_data_table import GanttDataTable
from taskdog.view_models.gantt_view_model import GanttViewModel
from taskdog_core.shared.constants.time import DAYS_PER_WEEK


class GanttWidget(VerticalScroll, TUIWidget):
    """A widget for displaying gantt chart using GanttDataTable.

    This widget manages the GanttDataTable and handles date range calculations
    based on available screen width.
    """

    # Allow maximize for this widget (same as TaskTable)
    allow_maximize = True

    # Add Vi-style bindings for scrolling
    BINDINGS: ClassVar = [
        Binding(
            "j",
            "scroll_down",
            "Scroll Down",
            show=False,
            tooltip="Scroll down one line (Vi-style)",
        ),
        Binding(
            "k",
            "scroll_up",
            "Scroll Up",
            show=False,
            tooltip="Scroll up one line (Vi-style)",
        ),
        Binding(
            "g", "scroll_home", "Top", show=False, tooltip="Scroll to top (Vi-style)"
        ),
        Binding(
            "G",
            "scroll_end",
            "Bottom",
            show=False,
            tooltip="Scroll to bottom (Vi-style)",
        ),
        Binding(
            "ctrl+d",
            "page_down",
            "Page Down",
            show=False,
            tooltip="Scroll down half a page (Vi-style)",
        ),
        Binding(
            "ctrl+u",
            "page_up",
            "Page Up",
            show=False,
            tooltip="Scroll up half a page (Vi-style)",
        ),
        Binding(
            "h",
            "scroll_left",
            "Scroll Left",
            show=False,
            tooltip="Scroll left (Vi-style)",
        ),
        Binding(
            "l",
            "scroll_right",
            "Scroll Right",
            show=False,
            tooltip="Scroll right (Vi-style)",
        ),
    ]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the gantt widget."""
        super().__init__(*args, **kwargs)
        self.can_focus = True
        self._task_ids: list[int] = []
        # NOTE: _gantt_view_model removed - now accessed via self.app.state.gantt_cache (Step 4)
        # NOTE: _sort_by and _reverse removed - now accessed via self.app.state (Step 2)
        self._filter_all: bool = False  # Include archived tasks flag for recalculation
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
        reverse: bool = False,
        all: bool = False,
    ):
        """Update the gantt chart with new gantt data.

        Args:
            task_ids: List of task IDs (used for recalculating date range on resize)
            gantt_view_model: Presentation-ready gantt data
            sort_by: Sort order for tasks (kept for compatibility, value comes from app.state)
            reverse: Sort direction (kept for compatibility, value comes from app.state)
            all: Include archived tasks (default: False)
        """
        self._task_ids = task_ids
        # Store gantt view model in app state (Step 4)
        self.tui_state.gantt_cache = gantt_view_model
        # NOTE: sort_by and reverse parameters kept for API compatibility,
        # but actual values are read from self.tui_state
        self._filter_all = all
        self._render_gantt()

    def _get_gantt_from_state(self) -> GanttViewModel | None:
        """Get gantt view model from app state.

        Returns:
            GanttViewModel from app state cache, or None if not available
        """
        return self.tui_state.gantt_cache

    def _render_gantt(self) -> None:
        """Render the gantt chart."""
        # Check if widget is mounted and table exists
        if not self.is_mounted or not self._gantt_table:
            return

        gantt_view_model = self._get_gantt_from_state()
        if not gantt_view_model or gantt_view_model.is_empty():
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
            if gantt_view_model:
                self._gantt_table.load_gantt(gantt_view_model)
                self._update_title()
                self._update_legend()
        except Exception as e:
            self._show_error_message(e)

    def _update_title(self) -> None:
        """Update title with date range and sort order."""
        if not self._title_widget:
            return

        gantt_view_model = self._get_gantt_from_state()
        if not gantt_view_model:
            return

        start_date = gantt_view_model.start_date
        end_date = gantt_view_model.end_date
        # Access sort state from tui_state
        arrow = "↓" if self.tui_state.sort_reverse else "↑"
        title_text = (
            f"[bold yellow]Gantt Chart[/bold yellow] "
            f"[dim]({start_date} to {end_date})[/dim] "
            f"[dim]- sorted by: {self.tui_state.sort_by} {arrow}[/dim]"
        )
        self._title_widget.update(title_text)

    def _update_legend(self) -> None:
        """Update legend with gantt chart symbols."""
        if not self._legend_widget:
            return

        legend_text = self._gantt_table.get_legend_text()
        self._legend_widget.update(legend_text)

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
        return weeks * DAYS_PER_WEEK

    def _calculate_date_range_for_display(self, display_days: int) -> tuple[date, date]:
        """Calculate start and end dates based on display days.

        Always starts from the previous Monday and extends by the specified number of days.

        Args:
            display_days: Number of days to display

        Returns:
            Tuple of (start_date, end_date)
        """
        today = date.today()
        start_date = today - timedelta(days=today.weekday())
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

    # Public API methods for external access

    def get_filter_all(self) -> bool:
        """Get current archive filter setting.

        Returns:
            Whether to include archived tasks
        """
        return self._filter_all

    def get_sort_by(self) -> str:
        """Get current sort order.

        Returns:
            Current sort field (e.g., "deadline", "priority")
        """
        # Access sort state from tui_state (single source of truth)
        return self.tui_state.sort_by

    def update_view_model_and_render(self, gantt_view_model) -> None:
        """Update gantt view model and trigger re-render.

        This method updates the internal view model and schedules a re-render
        after the next refresh cycle.

        Args:
            gantt_view_model: New GanttViewModel to display
        """
        # Store in app state (Step 4)
        self.tui_state.gantt_cache = gantt_view_model
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
