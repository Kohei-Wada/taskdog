from datetime import date, timedelta
from typing import Any

from rich.table import Table
from rich.text import Text

from presentation.console.console_writer import ConsoleWriter
from presentation.constants.colors import GANTT_COLUMN_EST_HOURS_COLOR
from presentation.constants.table_dimensions import (
    GANTT_TABLE_EST_HOURS_WIDTH,
    GANTT_TABLE_ID_WIDTH,
    GANTT_TABLE_TASK_MIN_WIDTH,
)
from presentation.constants.table_styles import (
    COLUMN_ID_STYLE,
    COLUMN_NAME_STYLE,
    TABLE_BORDER_STYLE,
    TABLE_HEADER_STYLE,
    TABLE_PADDING,
    format_table_title,
)
from presentation.renderers.gantt_cell_formatter import GanttCellFormatter
from presentation.renderers.rich_renderer_base import RichRendererBase
from presentation.view_models.gantt_view_model import GanttViewModel, TaskGanttRowViewModel


class RichGanttRenderer(RichRendererBase):
    """Renders GanttViewModel as a Rich table.

    This renderer is responsible solely for presentation logic:
    - Mapping GanttViewModel data to Rich Table format
    - Applying colors, styles, and visual formatting
    - Building the final table with legend

    All business logic (date calculations, workload aggregation) is handled
    by the Application layer. Presentation formatting (strikethrough, etc.)
    is applied by GanttPresenter when converting from GanttOutput to GanttViewModel.
    """

    def __init__(
        self,
        console_writer: ConsoleWriter,
    ):
        """Initialize the renderer.

        Args:
            console_writer: Console writer for output
        """
        self.console_writer = console_writer

    def build_table(self, gantt_view_model: GanttViewModel) -> Table | None:
        """Build and return a Gantt chart Table object from GanttViewModel.

        Args:
            gantt_view_model: Presentation-ready Gantt data

        Returns:
            Rich Table object or None if no tasks
        """
        if gantt_view_model.is_empty():
            return None

        start_date = gantt_view_model.start_date
        end_date = gantt_view_model.end_date

        # Create Rich table
        table = Table(
            title=format_table_title(f"Gantt Chart ({start_date} to {end_date})"),
            show_header=True,
            header_style=TABLE_HEADER_STYLE,
            border_style=TABLE_BORDER_STYLE,
            padding=TABLE_PADDING,
        )

        # Add columns
        table.add_column(
            "ID",
            justify="right",
            style=COLUMN_ID_STYLE,
            no_wrap=True,
            width=GANTT_TABLE_ID_WIDTH,
        )
        table.add_column("Task", style=COLUMN_NAME_STYLE, min_width=GANTT_TABLE_TASK_MIN_WIDTH)
        table.add_column(
            "Est.\\[h]",
            justify="right",
            style=GANTT_COLUMN_EST_HOURS_COLOR,
            no_wrap=True,
            width=GANTT_TABLE_EST_HOURS_WIDTH,
        )
        table.add_column("Timeline", style=COLUMN_NAME_STYLE)

        # Add date header row
        date_header = self._build_date_header(start_date, end_date, gantt_view_model.holidays)
        table.add_row("", "[dim]Date[/dim]", "", date_header)

        # Display all tasks in sort order
        for task_vm in gantt_view_model.tasks:
            task_daily_hours = gantt_view_model.task_daily_hours.get(task_vm.id, {})
            self._add_task_to_gantt(
                task_vm, task_daily_hours, table, start_date, end_date, gantt_view_model.holidays
            )

        # Add section divider before workload summary
        table.add_section()

        # Add workload summary row
        workload_timeline = self._build_workload_summary_row(
            gantt_view_model.daily_workload, start_date, end_date
        )
        table.add_row("", "[bold yellow]Workload\\[h][/bold yellow]", "", workload_timeline)

        # Add legend as caption (centered by default)
        legend_text = self._build_legend()
        table.caption = legend_text
        table.caption_justify = "center"

        return table

    def render(self, gantt_view_model: GanttViewModel) -> None:
        """Render and print Gantt chart from GanttViewModel.

        Args:
            gantt_view_model: Presentation-ready Gantt data
        """
        if gantt_view_model.is_empty():
            self.console_writer.warning("No tasks found.")
            return

        table = self.build_table(gantt_view_model)

        if table is None:
            self.console_writer.warning("No tasks found.")
            return

        # Print table (with caption as legend)
        self.console_writer.print(table)

    def _build_date_header(self, start_date: date, end_date: date, holidays: set[date]) -> Text:
        """Build date header row for the timeline.

        Args:
            start_date: Start date of the chart
            end_date: End date of the chart
            holidays: Set of holiday dates for styling

        Returns:
            Rich Text object with date labels (3 lines)
        """
        # Get the three header lines from the formatter
        month_line, today_line, day_line = GanttCellFormatter.build_date_header_lines(
            start_date, end_date, holidays
        )

        # Combine all three lines
        header = Text()
        header.append_text(month_line)
        header.append("\n")
        header.append_text(today_line)
        header.append("\n")
        header.append_text(day_line)

        return header

    def _add_task_to_gantt(
        self,
        task_vm: TaskGanttRowViewModel,
        task_daily_hours: dict[date, float],
        table: Table,
        start_date: date,
        end_date: date,
        holidays: set[date],
    ):
        """Add a task to Gantt chart table.

        Args:
            task_vm: Task ViewModel to add
            task_daily_hours: Daily hours allocation for this task
            table: Rich Table object
            start_date: Start date of the chart
            end_date: End date of the chart
            holidays: Set of holiday dates for styling
        """
        # Use pre-formatted name (strikethrough already applied by mapper)
        task_name = task_vm.formatted_name

        # Use pre-formatted estimated duration
        estimated_hours = task_vm.formatted_estimated_duration

        # Build timeline
        timeline = self._build_timeline(task_vm, task_daily_hours, start_date, end_date, holidays)

        table.add_row(str(task_vm.id), task_name, estimated_hours, timeline)

    def _build_timeline(
        self,
        task_vm: TaskGanttRowViewModel,
        task_daily_hours: dict[date, float],
        start_date: date,
        end_date: date,
        holidays: set[date],
    ) -> Text:
        """Build timeline visualization for a task using layered approach.

        Args:
            task_vm: Task ViewModel to build timeline for
            task_daily_hours: Daily hours allocation for this task
            start_date: Start date of the chart
            end_date: End date of the chart
            holidays: Set of holiday dates for styling

        Returns:
            Rich Text object with timeline visualization
        """
        days = (end_date - start_date).days + 1

        # Create parsed_dates dict from ViewModel (dates are already converted)
        parsed_dates: dict[str, Any] = {
            "planned_start": task_vm.planned_start,
            "planned_end": task_vm.planned_end,
            "actual_start": task_vm.actual_start,
            "actual_end": task_vm.actual_end,
            "deadline": task_vm.deadline,
        }

        # If no dates at all, show message
        if not any(parsed_dates.values()):
            return Text("(no dates)", style="dim")

        # Build timeline with daily hours displayed in each cell
        timeline = Text()
        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            hours = task_daily_hours.get(current_date, 0.0)

            # Determine cell display and styling using the formatter
            display, style = GanttCellFormatter.format_timeline_cell(
                current_date, hours, parsed_dates, task_vm.status, holidays
            )

            timeline.append(display, style=style)

        return timeline

    def _build_legend(self) -> Text:
        """Build the legend text for the Gantt chart.

        Returns:
            Rich Text object with legend
        """
        return GanttCellFormatter.build_legend()

    def _build_workload_summary_row(
        self, daily_workload: dict[date, float], start_date: date, end_date: date
    ) -> Text:
        """Build workload summary timeline showing daily total hours.

        Args:
            daily_workload: Pre-computed daily workload totals
            start_date: Start date of the chart
            end_date: End date of the chart

        Returns:
            Rich Text object with workload summary
        """
        return GanttCellFormatter.build_workload_timeline(daily_workload, start_date, end_date)
