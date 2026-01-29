"""Rich-based renderer for Timeline chart.

This module renders the Timeline chart as a Rich Table, showing
actual work times on a horizontal time axis for a specific day.
"""

from rich.table import Table
from rich.text import Text

from taskdog.console.console_writer import ConsoleWriter
from taskdog.constants.table_dimensions import (
    GANTT_TABLE_ID_WIDTH,
    GANTT_TABLE_TASK_MIN_WIDTH,
)
from taskdog.constants.table_styles import (
    COLUMN_ID_STYLE,
    COLUMN_NAME_STYLE,
    TABLE_BORDER_STYLE,
    TABLE_HEADER_STYLE,
    TABLE_PADDING,
    format_table_title,
)
from taskdog.renderers.rich_renderer_base import RichRendererBase
from taskdog.renderers.timeline_cell_formatter import (
    CHARS_PER_HOUR,
    TimelineCellFormatter,
)
from taskdog.view_models.timeline_view_model import (
    TimelineTaskRowViewModel,
    TimelineViewModel,
)

# Column width for duration display
TIMELINE_TABLE_DURATION_WIDTH = 6


class RichTimelineRenderer(RichRendererBase):
    """Renders TimelineViewModel as a Rich table.

    This renderer displays actual work times on a horizontal time axis,
    showing when tasks were worked on during a specific day.
    """

    def __init__(self, console_writer: ConsoleWriter):
        """Initialize the renderer.

        Args:
            console_writer: Console writer for output
        """
        self.console_writer = console_writer

    def build_table(self, timeline_vm: TimelineViewModel) -> Table | None:
        """Build and return a Timeline chart Table object.

        Args:
            timeline_vm: Presentation-ready Timeline data

        Returns:
            Rich Table object or None if no tasks
        """
        if timeline_vm.is_empty():
            return None

        table = self._create_table(timeline_vm)
        self._add_columns(table)
        self._add_hour_header_row(table, timeline_vm)
        self._add_task_rows(table, timeline_vm)
        self._add_summary_section(table, timeline_vm)

        return table

    def _create_table(self, timeline_vm: TimelineViewModel) -> Table:
        """Create and configure the base Table object.

        Args:
            timeline_vm: Timeline data for title generation

        Returns:
            Configured Rich Table object
        """
        # Format date with day of week
        date_str = timeline_vm.target_date.strftime("%Y-%m-%d (%a)")

        return Table(
            title=format_table_title(f"Timeline - {date_str}"),
            show_header=True,
            header_style=TABLE_HEADER_STYLE,
            border_style=TABLE_BORDER_STYLE,
            padding=TABLE_PADDING,
        )

    def _add_columns(self, table: Table) -> None:
        """Add column definitions to the table.

        Args:
            table: Rich Table object to add columns to
        """
        table.add_column(
            "ID",
            justify="right",
            style=COLUMN_ID_STYLE,
            no_wrap=True,
            width=GANTT_TABLE_ID_WIDTH,
        )
        table.add_column(
            "Task", style=COLUMN_NAME_STYLE, min_width=GANTT_TABLE_TASK_MIN_WIDTH
        )
        table.add_column("Timeline", style=COLUMN_NAME_STYLE)
        table.add_column(
            "Time",
            justify="right",
            style="cyan",
            no_wrap=True,
            width=TIMELINE_TABLE_DURATION_WIDTH,
        )

    def _add_hour_header_row(
        self, table: Table, timeline_vm: TimelineViewModel
    ) -> None:
        """Add the hour header row to the table.

        Args:
            table: Rich Table object
            timeline_vm: Timeline data containing time range
        """
        hour_header = TimelineCellFormatter.build_hour_header(
            timeline_vm.start_hour, timeline_vm.end_hour
        )
        table.add_row("", "[dim]Hour[/dim]", hour_header, "")

    def _add_task_rows(self, table: Table, timeline_vm: TimelineViewModel) -> None:
        """Add all task rows to the table.

        Args:
            table: Rich Table object
            timeline_vm: Timeline data containing tasks
        """
        for row_vm in timeline_vm.rows:
            self._add_task_row(
                table,
                row_vm,
                timeline_vm.start_hour,
                timeline_vm.end_hour,
            )

    def _add_task_row(
        self,
        table: Table,
        row_vm: TimelineTaskRowViewModel,
        start_hour: int,
        end_hour: int,
    ) -> None:
        """Add a single task row to the table.

        Args:
            table: Rich Table object
            row_vm: Task row ViewModel
            start_hour: Display start hour
            end_hour: Display end hour
        """
        # Build timeline bar
        timeline_bar = TimelineCellFormatter.build_timeline_bar(
            row_vm.actual_start,
            row_vm.actual_end,
            start_hour,
            end_hour,
            row_vm.status,
        )

        # Format duration
        duration_str = TimelineCellFormatter.format_duration(row_vm.duration_hours)

        table.add_row(
            str(row_vm.task_id),
            row_vm.formatted_name,
            timeline_bar,
            duration_str,
        )

    def _add_summary_section(
        self, table: Table, timeline_vm: TimelineViewModel
    ) -> None:
        """Add section divider and summary row.

        Args:
            table: Rich Table object
            timeline_vm: Timeline data containing totals
        """
        table.add_section()

        # Build summary text
        summary_text = (
            f"[bold yellow]{timeline_vm.task_count} tasks | "
            f"{timeline_vm.total_work_hours:.1f}h worked[/bold yellow]"
        )

        # Calculate timeline width for centering
        timeline_width = (
            timeline_vm.end_hour - timeline_vm.start_hour + 1
        ) * CHARS_PER_HOUR

        # Create centered summary in timeline column
        summary_timeline = Text()
        padding = max(
            0,
            (
                timeline_width
                - len(
                    f"{timeline_vm.task_count} tasks | {timeline_vm.total_work_hours:.1f}h worked"
                )
            )
            // 2,
        )
        summary_timeline.append(" " * padding)

        table.add_row(
            "",
            "[bold yellow]Summary[/bold yellow]",
            summary_text,
            "",
        )

        # Add legend
        legend_text = TimelineCellFormatter.build_legend()
        table.caption = legend_text
        table.caption_justify = "center"

    def render(self, timeline_vm: TimelineViewModel) -> None:
        """Render and print Timeline chart from TimelineViewModel.

        Args:
            timeline_vm: Presentation-ready Timeline data
        """
        if timeline_vm.is_empty():
            date_str = timeline_vm.target_date.strftime("%Y-%m-%d (%a)")
            self.console_writer.warning(
                f"No tasks with actual work times found for {date_str}."
            )
            return

        table = self.build_table(timeline_vm)

        if table is None:
            self.console_writer.warning("No tasks found.")
            return

        self.console_writer.print(table)
