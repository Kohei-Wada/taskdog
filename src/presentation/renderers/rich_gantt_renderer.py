import math
from datetime import date, timedelta

from rich.table import Table
from rich.text import Text

from application.dto.gantt_result import GanttResult
from domain.entities.task import Task, TaskStatus
from presentation.console.console_writer import ConsoleWriter
from presentation.constants.colors import (
    DAY_STYLE_SATURDAY,
    DAY_STYLE_SUNDAY,
    DAY_STYLE_WEEKDAY,
    GANTT_COLUMN_EST_HOURS_COLOR,
)
from presentation.constants.symbols import (
    BACKGROUND_COLOR,
    BACKGROUND_COLOR_DEADLINE,
    BACKGROUND_COLOR_SATURDAY,
    BACKGROUND_COLOR_SUNDAY,
    SYMBOL_ACTUAL,
    SYMBOL_EMPTY,
    SYMBOL_TODAY,
)
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
from presentation.renderers.rich_renderer_base import RichRendererBase
from shared.constants import SATURDAY, SUNDAY, WORKLOAD_COMFORTABLE_HOURS, WORKLOAD_MODERATE_HOURS
from shared.utils.date_utils import DateTimeParser


class RichGanttRenderer(RichRendererBase):
    """Renders GanttResult as a Rich table.

    This renderer is responsible solely for presentation logic:
    - Mapping GanttResult data to Rich Table format
    - Applying colors, styles, and visual formatting
    - Building the final table with legend

    All business logic (date calculations, workload aggregation) is handled
    by the Application layer (TaskQueryService.get_gantt_data()).
    """

    def __init__(self, console_writer: ConsoleWriter):
        """Initialize the renderer.

        Args:
            console_writer: Console writer for output
        """
        self.console_writer = console_writer

    def build_table(self, gantt_result: GanttResult) -> Table | None:
        """Build and return a Gantt chart Table object from GanttResult.

        Args:
            gantt_result: Pre-computed Gantt data from Application layer

        Returns:
            Rich Table object or None if no tasks
        """
        if gantt_result.is_empty():
            return None

        start_date = gantt_result.date_range.start_date
        end_date = gantt_result.date_range.end_date

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
        date_header = self._build_date_header(start_date, end_date)
        table.add_row("", "[dim]Date[/dim]", "", date_header)

        # Display all tasks in sort order
        for task in gantt_result.tasks:
            task_daily_hours = gantt_result.task_daily_hours.get(task.id, {})
            self._add_task_to_gantt(task, task_daily_hours, table, start_date, end_date)

        # Add section divider before workload summary
        table.add_section()

        # Add workload summary row
        workload_timeline = self._build_workload_summary_row(
            gantt_result.daily_workload, start_date, end_date
        )
        table.add_row("", "[bold yellow]Workload\\[h][/bold yellow]", "", workload_timeline)

        # Add legend as caption (centered by default)
        legend_text = self._build_legend()
        table.caption = legend_text
        table.caption_justify = "center"

        return table

    def render(self, gantt_result: GanttResult) -> None:
        """Render and print Gantt chart from GanttResult.

        Args:
            gantt_result: Pre-computed Gantt data from Application layer
        """
        if gantt_result.is_empty():
            self.console_writer.warning("No tasks found.")
            return

        table = self.build_table(gantt_result)

        if table is None:
            self.console_writer.warning("No tasks found.")
            return

        # Print table (with caption as legend)
        self.console_writer.print(table)

    def _build_date_header(self, start_date: date, end_date: date) -> Text:
        """Build date header row for the timeline.

        Args:
            start_date: Start date of the chart
            end_date: End date of the chart

        Returns:
            Rich Text object with date labels (2 lines)
        """
        days = (end_date - start_date).days + 1

        # Line 1: Month indicators
        line1 = Text()
        # Line 2: Today marker
        line2 = Text()
        # Line 3: Day numbers
        line3 = Text()

        current_month = None
        today = date.today()
        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            month = current_date.month
            day = current_date.day
            weekday = current_date.weekday()
            is_today = current_date == today

            # Line 1: Show month when it changes
            if month != current_month:
                month_str = current_date.strftime("%b")  # e.g., "Oct", "Nov"
                line1.append(month_str, style="bold yellow")
                # Pad the rest of the month's days
                current_month = month
            else:
                line1.append("   ", style="dim")

            # Line 2: Show yellow circle marker for today
            if is_today:
                line2.append(f" {SYMBOL_TODAY} ", style="bold yellow")
            else:
                line2.append("   ", style="dim")

            # Line 3: Show day number with color based on weekday
            day_str = f"{day:2d} "  # Right-aligned, 2 digits + space
            if weekday == SATURDAY:
                day_style = DAY_STYLE_SATURDAY
            elif weekday == SUNDAY:
                day_style = DAY_STYLE_SUNDAY
            else:  # Weekday
                day_style = DAY_STYLE_WEEKDAY
            line3.append(day_str, style=day_style)

        # Combine all three lines
        header = Text()
        header.append_text(line1)
        header.append("\n")
        header.append_text(line2)
        header.append("\n")
        header.append_text(line3)

        return header

    def _add_task_to_gantt(
        self,
        task: Task,
        task_daily_hours: dict[date, float],
        table: Table,
        start_date: date,
        end_date: date,
    ):
        """Add a task to Gantt chart table.

        Args:
            task: Task to add
            task_daily_hours: Daily hours allocation for this task
            table: Rich Table object
            start_date: Start date of the chart
            end_date: End date of the chart
        """
        task_name = task.name

        # Add strikethrough for completed tasks
        if task.status == TaskStatus.COMPLETED:
            task_name = f"[strike]{task_name}[/strike]"

        # Format estimated duration
        estimated_hours = self._format_estimated_hours(task.estimated_duration)

        # Build timeline
        timeline = self._build_timeline(task, task_daily_hours, start_date, end_date)

        table.add_row(str(task.id), task_name, estimated_hours, timeline)

    def _build_timeline(
        self,
        task: Task,
        task_daily_hours: dict[date, float],
        start_date: date,
        end_date: date,
    ) -> Text:
        """Build timeline visualization for a task using layered approach.

        Args:
            task: Task to build timeline for
            task_daily_hours: Daily hours allocation for this task
            start_date: Start date of the chart
            end_date: End date of the chart

        Returns:
            Rich Text object with timeline visualization
        """
        days = (end_date - start_date).days + 1

        # Parse task dates
        parsed_dates = self._parse_task_dates(task)

        # If no dates at all, show message
        if not any(parsed_dates.values()):
            return Text("(no dates)", style="dim")

        # Build timeline with daily hours displayed in each cell
        timeline = Text()
        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            hours = task_daily_hours.get(current_date, 0.0)

            # Determine cell display and styling
            display, style = self._format_timeline_cell(
                current_date, hours, parsed_dates, task.status
            )

            timeline.append(display, style=style)

        return timeline

    def _format_timeline_cell(
        self,
        current_date: date,
        hours: float,
        parsed_dates: dict,
        status: str,
    ) -> tuple[str, str]:
        """Format a single timeline cell with daily hours and styling.

        Args:
            current_date: Date of the cell
            hours: Allocated hours for this date
            parsed_dates: Dictionary of parsed task dates
            status: Task status

        Returns:
            Tuple of (display_text, style_string)
        """
        # Check if date is in special periods
        is_planned = self._is_in_date_range(
            current_date, parsed_dates["planned_start"], parsed_dates["planned_end"]
        )

        # For actual period: if actual_end is None (IN_PROGRESS), treat actual_start to today as actual period
        if parsed_dates["actual_start"] and not parsed_dates["actual_end"]:
            # IN_PROGRESS: actual_start to today is actual period
            today = date.today()
            is_actual = parsed_dates["actual_start"] <= current_date <= today
        else:
            # COMPLETED: actual_start to actual_end is actual period
            is_actual = self._is_in_date_range(
                current_date, parsed_dates["actual_start"], parsed_dates["actual_end"]
            )

        is_deadline = parsed_dates["deadline"] and current_date == parsed_dates["deadline"]

        # Determine background color (deadline gets orange background)
        # COMPLETED tasks: hide planned period background (only show actual and deadline)
        if is_deadline:
            bg_color = BACKGROUND_COLOR_DEADLINE
        elif is_planned and status != TaskStatus.COMPLETED:
            bg_color = self._get_background_color(current_date)
        else:
            bg_color = None

        # Layer 2: Actual period (highest priority for display) - use symbol
        if is_actual:
            display = f" {SYMBOL_ACTUAL} "
            status_color = self._get_status_color(status)
            style = f"{status_color} on {bg_color}" if bg_color else status_color
            return display, style

        # Layer 1: Show hours (for planned or deadline without actual)
        # COMPLETED tasks: hide planned hours (only show actual period and deadline)
        if hours > 0 and status != TaskStatus.COMPLETED:
            # Format: "4  " or "2.5" (right-aligned, 3 chars)
            display = f"{int(hours):2d} " if hours == int(hours) else f"{hours:3.1f}"
        else:
            display = SYMBOL_EMPTY  # No hours allocated: " · "

        # Apply background color
        style = f"on {bg_color}" if bg_color else "dim"

        return display, style

    def _parse_task_dates(self, task: Task) -> dict:
        """Parse all task dates into a dictionary.

        Args:
            task: Task to parse dates from

        Returns:
            Dictionary with parsed dates (planned_start, planned_end, actual_start, actual_end, deadline)
        """
        return {
            "planned_start": DateTimeParser.parse_date(task.planned_start),
            "planned_end": DateTimeParser.parse_date(task.planned_end),
            "actual_start": DateTimeParser.parse_date(task.actual_start),
            "actual_end": DateTimeParser.parse_date(task.actual_end),
            "deadline": DateTimeParser.parse_date(task.deadline),
        }

    def _is_in_date_range(self, current_date: date, start: date | None, end: date | None) -> bool:
        """Check if a date is within a range.

        Args:
            current_date: Date to check
            start: Start of range (inclusive)
            end: End of range (inclusive)

        Returns:
            True if current_date is within range
        """
        if start and end:
            return start <= current_date <= end
        return False

    def _get_background_color(self, current_date: date) -> str:
        """Get background color based on day of week.

        Args:
            current_date: Date to check

        Returns:
            Background color string (RGB)
        """
        weekday = current_date.weekday()
        if weekday == SATURDAY:
            return BACKGROUND_COLOR_SATURDAY
        elif weekday == SUNDAY:
            return BACKGROUND_COLOR_SUNDAY
        else:
            return BACKGROUND_COLOR

    def _format_estimated_hours(self, estimated_duration: float | None) -> str:
        """Format estimated duration for display.

        Args:
            estimated_duration: Estimated duration in hours (can be None)

        Returns:
            Formatted string (e.g., "8.0", "-")
        """
        if estimated_duration is None:
            return "-"
        return f"{estimated_duration:.1f}"

    def _build_legend(self) -> Text:
        """Build the legend text for the Gantt chart.

        Returns:
            Rich Text object with legend
        """
        legend = Text()
        legend.append("Legend: ", style="bold yellow")
        legend.append("   ", style=f"on {BACKGROUND_COLOR}")
        legend.append(" Planned  ", style="dim")
        legend.append(SYMBOL_ACTUAL, style="bold blue")
        legend.append(" Actual (IN_PROGRESS)  ", style="dim")
        legend.append(SYMBOL_ACTUAL, style="bold green")
        legend.append(" Actual (COMPLETED)  ", style="dim")
        legend.append("   ", style=f"on {BACKGROUND_COLOR_DEADLINE}")
        legend.append(" Deadline  ", style="dim")
        legend.append(SYMBOL_TODAY, style="bold yellow")
        legend.append(" Today  ", style="dim")
        legend.append("   ", style=f"on {BACKGROUND_COLOR_SATURDAY}")
        legend.append(" Saturday  ", style="dim")
        legend.append("   ", style=f"on {BACKGROUND_COLOR_SUNDAY}")
        legend.append(" Sunday", style="dim")
        return legend

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
        days = (end_date - start_date).days + 1

        timeline = Text()
        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            hours = daily_workload.get(current_date, 0.0)

            # Format hours display (3 characters for consistency)
            # Ceil to round up (e.g., 4.3 -> 5, 4.0 -> 4)
            hours_ceiled = math.ceil(hours)

            # Format with consistent width (3 characters, right-aligned)
            display = f"{hours_ceiled:2d} "

            # Color based on workload level (use original hours for threshold)
            if hours == 0:
                style = "dim"
            elif hours <= WORKLOAD_COMFORTABLE_HOURS:
                style = "bold green"
            elif hours <= WORKLOAD_MODERATE_HOURS:
                style = "bold yellow"
            else:
                style = "bold red"

            timeline.append(display, style=style)

        return timeline
