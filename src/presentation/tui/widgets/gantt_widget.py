"""Gantt chart widget for TUI.

This widget wraps the GanttDataTable and provides additional functionality
like date range management and automatic resizing.
"""

from contextlib import suppress
from datetime import date, timedelta

from textual.app import ComposeResult
from textual.containers import Center, VerticalScroll
from textual.widgets import Static

from application.dto.gantt_result import GanttResult
from presentation.constants.table_dimensions import (
    BORDER_WIDTH,
    CHARS_PER_DAY,
    DEFAULT_GANTT_WIDGET_WIDTH,
    GANTT_TABLE_FIXED_WIDTH,
    MIN_CONSOLE_WIDTH,
    MIN_TIMELINE_WIDTH,
)
from presentation.tui.widgets.gantt_data_table import GanttDataTable
from shared.config_manager import Config
from shared.constants.time import DAYS_PER_WEEK
from shared.utils.date_utils import get_previous_monday
from shared.utils.holiday_checker import HolidayChecker


class GanttWidget(VerticalScroll):
    """A widget for displaying gantt chart using GanttDataTable.

    This widget manages the GanttDataTable and handles date range calculations
    based on available screen width.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the gantt widget."""
        super().__init__(*args, **kwargs)
        self._task_ids: list[int] = []
        self._gantt_result: GanttResult | None = None
        self._sort_by: str = "deadline"  # Default sort order
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

        # Create HolidayChecker from app config
        holiday_checker = self._create_holiday_checker()
        self._gantt_table = GanttDataTable(holiday_checker=holiday_checker, id="gantt-table")
        self._gantt_table.styles.width = "auto"

        # Wrap table in Center container for horizontal centering
        with Center():
            yield self._gantt_table

        # Legend below the table
        self._legend_widget = Static("")
        self._legend_widget.styles.text_align = "center"
        self._legend_widget.styles.margin = (1, 0, 0, 0)  # Top margin
        yield self._legend_widget

    def _create_holiday_checker(self) -> HolidayChecker | None:
        """Create HolidayChecker from app config.

        Returns:
            HolidayChecker instance if country is configured, None otherwise
        """
        # Access app config via self.app
        with suppress(AttributeError):
            # Type hint: app is TaskdogTUI which has config attribute
            app = self.app  # type: ignore[attr-defined]
            config: Config = app.config

            if config.region.country:
                with suppress(ImportError, NotImplementedError):
                    return HolidayChecker(config.region.country)

        return None

    def update_gantt(
        self,
        task_ids: list[int],
        gantt_result: GanttResult,
        sort_by: str = "deadline",
    ):
        """Update the gantt chart with new gantt data.

        Args:
            task_ids: List of task IDs (used for recalculating date range on resize)
            gantt_result: Pre-computed gantt data from TaskService
            sort_by: Sort order for tasks (default: "deadline")
        """
        self._task_ids = task_ids
        self._gantt_result = gantt_result
        self._sort_by = sort_by
        self._render_gantt()

    def _render_gantt(self):
        """Render the gantt chart."""
        if not self._gantt_table:
            return

        if not self._gantt_result or self._gantt_result.is_empty():
            self._show_empty_message()
            return

        # Directly load the pre-computed gantt result
        self._load_gantt_data()

    def update(self, message: str) -> None:
        """Update the gantt widget with a message.

        Args:
            message: Message to display
        """
        if self._gantt_table:
            self._gantt_table.clear(columns=True)
            self._gantt_table.add_column("Message")
            self._gantt_table.add_row(message)

    def _show_empty_message(self):
        """Show empty message when no tasks are available."""
        self._gantt_table.clear(columns=True)
        self._gantt_table.add_column("Message")
        self._gantt_table.add_row("[dim]No tasks to display[/dim]")

    def _load_gantt_data(self):
        """Load and display gantt data from the pre-computed gantt result."""
        try:
            self._gantt_table.load_gantt(self._gantt_result)

            # Update title with date range and sort order
            if self._title_widget:
                start_date = self._gantt_result.date_range.start_date
                end_date = self._gantt_result.date_range.end_date
                title_text = (
                    f"[bold yellow]Gantt Chart[/bold yellow] "
                    f"[dim]({start_date} to {end_date})[/dim] "
                    f"[dim]- sorted by: {self._sort_by}[/dim]"
                )
                self._title_widget.update(title_text)

            # Update legend
            if self._legend_widget:
                legend_text = self._gantt_table.get_legend_text()
                self._legend_widget.update(legend_text)
        except Exception as e:
            self._show_error_message(e)

    def _show_error_message(self, error: Exception):
        """Show error message when rendering fails.

        Args:
            error: The exception that occurred
        """
        self._gantt_table.clear(columns=True)
        self._gantt_table.add_column("Error")
        self._gantt_table.add_row(f"[red]Error rendering gantt: {error!s}[/red]")
        if self._title_widget:
            self._title_widget.update("")
        if self._legend_widget:
            self._legend_widget.update("")

    def _calculate_display_days(self) -> int:
        """Calculate optimal number of days to display.

        Returns:
            Number of days to display (rounded to weeks)
        """
        widget_width = self.size.width if self.size else DEFAULT_GANTT_WIDGET_WIDTH
        console_width = max(widget_width - BORDER_WIDTH, MIN_CONSOLE_WIDTH)
        timeline_width = max(console_width - GANTT_TABLE_FIXED_WIDTH, MIN_TIMELINE_WIDTH)
        max_days = timeline_width // CHARS_PER_DAY
        weeks = max(max_days // DAYS_PER_WEEK, 1)
        return weeks * DAYS_PER_WEEK

    def _calculate_date_range_for_display(self, display_days: int) -> tuple[date, date]:
        """Calculate start and end dates based on display days and current gantt result.

        Args:
            display_days: Number of days to display

        Returns:
            Tuple of (start_date, end_date)
        """
        if not self._gantt_result:
            # No gantt result yet, use default range
            start_date = get_previous_monday()
            end_date = start_date + timedelta(days=display_days - 1)
            return start_date, end_date

        # Always recalculate date range based on new display_days
        # to properly handle screen width changes
        start_date = get_previous_monday()
        end_date = start_date + timedelta(days=display_days - 1)
        return start_date, end_date

    def on_resize(self):
        """Handle resize events."""
        if self._task_ids and self._gantt_result:
            # Recalculate appropriate date range for new screen width
            display_days = self._calculate_display_days()
            start_date, end_date = self._calculate_date_range_for_display(display_days)

            # Request new gantt data with adjusted date range via app
            try:
                app = self.app  # type: ignore[attr-defined]
                gantt_result = app.task_service.get_gantt_data(
                    task_ids=self._task_ids,
                    sort_by=self._sort_by,
                    start_date=start_date,
                    end_date=end_date,
                )
                self._gantt_result = gantt_result
                self.call_after_refresh(self._render_gantt)
            except AttributeError:
                # App not available, just re-render with existing data
                self.call_after_refresh(self._render_gantt)
