import math
from datetime import date, datetime, timedelta

from rich.table import Table
from rich.text import Text

from domain.entities.task import Task, TaskStatus
from domain.services.workload_calculator import WorkloadCalculator
from presentation.console.console_writer import ConsoleWriter
from presentation.renderers.constants import DATETIME_FORMAT
from presentation.renderers.rich_renderer_base import RichRendererBase
from shared.utils.date_utils import DateTimeParser


class RichGanttRenderer(RichRendererBase):
    """Renders tasks as a Gantt chart using Rich."""

    # Visual constants for Gantt chart symbols
    SYMBOL_PLANNED = "░"
    SYMBOL_ACTUAL = "◆"
    SYMBOL_EMPTY = " · "
    SYMBOL_EMPTY_SPACE = "   "  # 3 spaces for planned background

    # Background colors
    BACKGROUND_COLOR = "rgb(100,100,100)"  # Weekday
    BACKGROUND_COLOR_SATURDAY = "rgb(100,100,150)"  # Saturday (blueish)
    BACKGROUND_COLOR_SUNDAY = "rgb(150,100,100)"  # Sunday (reddish)
    BACKGROUND_COLOR_DEADLINE = "rgb(200,100,0)"  # Deadline (orange)

    def __init__(self, console_writer: ConsoleWriter):
        """Initialize the renderer.

        Args:
            console_writer: Console writer for output
        """
        self.console_writer = console_writer
        self.workload_calculator = WorkloadCalculator()

    def render(
        self,
        tasks: list[Task],
        repository,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> None:
        """Render and print tasks as a Gantt chart with Rich.

        Args:
            tasks: List of all tasks
            repository: Repository instance for accessing task relationships
            start_date: Optional start date for the chart (overrides auto-calculation)
            end_date: Optional end date for the chart (overrides auto-calculation)
        """
        if not tasks:
            self.console_writer.warning("No tasks found.")
            return

        # Calculate date range for the chart
        date_range = self._calculate_date_range(tasks, start_date, end_date)

        if date_range is None:
            # No tasks with dates - just show task names
            return self._format_tasks_without_dates(tasks, repository)

        start_date, end_date = date_range

        # Create Rich table
        table = Table(
            title=f"[bold cyan]Gantt Chart[/bold cyan] ({start_date} to {end_date})",
            show_header=True,
            header_style="bold magenta",
            border_style="bright_blue",
            padding=(0, 1),
        )

        # Add columns
        table.add_column("ID", justify="right", style="cyan", no_wrap=True, width=4)
        table.add_column("Task", style="white", min_width=20)
        table.add_column("Est.\\[h]", justify="right", style="yellow", no_wrap=True, width=7)
        table.add_column("Timeline", style="white")

        # Add date header row
        date_header = self._build_date_header(start_date, end_date)
        table.add_row("", "[dim]Date[/dim]", "", date_header)

        # Display all tasks in sort order
        for task in tasks:
            self._add_leaf_task_to_gantt(task, table, repository, start_date, end_date)

        # Add section divider before workload summary
        table.add_section()

        # Add workload summary row
        workload_timeline = self._build_workload_summary_row(tasks, start_date, end_date)
        table.add_row("", "[bold yellow]Workload\\[h][/bold yellow]", "", workload_timeline)

        # Print table and legend
        self.console_writer.print(table)
        self.console_writer.empty_line()
        legend_text = self._build_legend()
        self.console_writer.print(legend_text)

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
                line2.append(" ● ", style="bold yellow")
            else:
                line2.append("   ", style="dim")

            # Line 3: Show day number with color based on weekday
            day_str = f"{day:2d} "  # Right-aligned, 2 digits + space
            if weekday == 5:  # Saturday
                day_style = "blue"
            elif weekday == 6:  # Sunday
                day_style = "red"
            else:  # Weekday
                day_style = "cyan"
            line3.append(day_str, style=day_style)

        # Combine all three lines
        header = Text()
        header.append_text(line1)
        header.append("\n")
        header.append_text(line2)
        header.append("\n")
        header.append_text(line3)

        return header

    def _calculate_date_range(
        self,
        tasks: list[Task],
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> tuple[date, date] | None:
        """Calculate the date range for the Gantt chart.

        Args:
            tasks: List of tasks
            start_date: Optional start date to override auto-calculation
            end_date: Optional end date to override auto-calculation

        Returns:
            Tuple of (start_date, end_date) or None if no dates found
        """
        # If both dates are provided, use them directly
        if start_date and end_date:
            return start_date, end_date

        # Collect dates from tasks
        dates = []
        for task in tasks:
            # Collect all date fields
            for date_str in [
                task.planned_start,
                task.planned_end,
                task.actual_start,
                task.actual_end,
                task.deadline,
            ]:
                if date_str:
                    try:
                        dt = datetime.strptime(date_str, DATETIME_FORMAT)
                        dates.append(dt.date())
                    except ValueError:
                        pass

        if not dates:
            return None

        # Calculate min/max from tasks
        auto_start = min(dates)
        auto_end = max(dates)

        # Use provided dates if available, otherwise use auto-calculated
        final_start = start_date if start_date else auto_start
        final_end = end_date if end_date else auto_end

        return final_start, final_end

    def _format_tasks_without_dates(self, tasks: list[Task], repository) -> str:
        """Format tasks when no date information is available.

        Args:
            tasks: List of tasks
            repository: Repository instance

        Returns:
            Formatted string
        """
        # Create simple table with just task names
        table = Table(
            title="[bold cyan]Tasks (No dates available)[/bold cyan]",
            show_header=True,
            header_style="bold magenta",
            border_style="bright_blue",
        )

        table.add_column("ID", justify="right", style="cyan", no_wrap=True)
        table.add_column("Task", style="white")
        table.add_column("Status", justify="center")

        for task in tasks:
            self._add_simple_task(task, table, repository)

        self.console_writer.print(table)

    def _add_simple_task(self, task: Task, table: Table, repository):
        """Add task to simple table (no dates).

        Args:
            task: Task to add
            table: Rich Table object
            repository: Repository instance
        """
        status_style = self._get_status_style(task.status)
        status_text = f"[{status_style}]{task.status.value}[/{status_style}]"

        table.add_row(str(task.id), task.name, status_text)

    def _add_leaf_task_to_gantt(
        self,
        task: Task,
        table: Table,
        repository,
        start_date: date,
        end_date: date,
    ):
        """Add a task to Gantt chart table.

        Args:
            task: Task to add
            table: Rich Table object
            repository: Repository instance
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
        timeline = self._build_timeline(task, start_date, end_date, repository)

        table.add_row(str(task.id), task_name, estimated_hours, timeline)

    def _calculate_task_daily_hours(
        self, task: Task, start_date: date, end_date: date, repository
    ) -> dict:
        """Calculate daily hours allocation for a single task.

        Uses task.daily_allocations if available (from optimization),
        otherwise distributes estimated_duration equally across weekdays
        in the planned period.

        Args:
            task: Task to calculate daily hours for
            start_date: Start date of the chart
            end_date: End date of the chart
            repository: Repository instance (unused, kept for compatibility)

        Returns:
            Dictionary mapping date to hours {date: float}
        """
        days = (end_date - start_date).days + 1
        daily_hours = {start_date + timedelta(days=i): 0.0 for i in range(days)}

        # Skip tasks without estimated duration
        if not task.estimated_duration:
            return daily_hours

        # Use daily_allocations if available (from optimization)
        if task.daily_allocations:
            for date_str, hours in task.daily_allocations.items():
                try:
                    task_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    if task_date in daily_hours:
                        daily_hours[task_date] = hours
                except ValueError:
                    # Skip invalid date strings
                    pass
            return daily_hours

        # Fallback: distribute equally across weekdays in planned period
        if not (task.planned_start and task.planned_end):
            return daily_hours

        planned_start = DateTimeParser.parse_date(task.planned_start)
        planned_end = DateTimeParser.parse_date(task.planned_end)

        if not (planned_start and planned_end):
            return daily_hours

        # Count weekdays in the task's planned period
        weekday_count = self._count_weekdays(planned_start, planned_end)

        if weekday_count == 0:
            return daily_hours

        # Distribute hours equally across weekdays
        hours_per_day = task.estimated_duration / weekday_count

        # Add to each weekday in the period
        current_date = planned_start
        while current_date <= planned_end:
            # Skip weekends and add hours to weekdays in range
            if current_date.weekday() < 5 and current_date in daily_hours:  # Monday=0, Friday=4
                daily_hours[current_date] = hours_per_day
            current_date += timedelta(days=1)

        return daily_hours

    def _count_weekdays(self, start: date, end: date) -> int:
        """Count weekdays (Monday-Friday) in a date range.

        Args:
            start: Start date (inclusive)
            end: End date (inclusive)

        Returns:
            Number of weekdays in the range
        """
        weekday_count = 0
        current_date = start
        while current_date <= end:
            # Skip weekends (Saturday=5, Sunday=6)
            if current_date.weekday() < 5:
                weekday_count += 1
            current_date += timedelta(days=1)
        return weekday_count

    def _build_timeline(self, task: Task, start_date: date, end_date: date, repository) -> Text:
        """Build timeline visualization for a task using layered approach.

        Args:
            task: Task to build timeline for
            start_date: Start date of the chart
            end_date: End date of the chart
            repository: Repository instance for checking task relationships

        Returns:
            Rich Text object with timeline visualization
        """
        days = (end_date - start_date).days + 1

        # Parse task dates
        parsed_dates = self._parse_task_dates(task)

        # If no dates at all, show message
        if not any(parsed_dates.values()):
            return Text("(no dates)", style="dim")

        # Calculate daily hours for this task
        daily_hours = self._calculate_task_daily_hours(task, start_date, end_date, repository)

        # Build timeline with daily hours displayed in each cell
        timeline = Text()
        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            hours = daily_hours.get(current_date, 0.0)

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
        if is_deadline:
            bg_color = self.BACKGROUND_COLOR_DEADLINE
        elif is_planned:
            bg_color = self._get_background_color(current_date)
        else:
            bg_color = None

        # Layer 2: Actual period (highest priority for display) - use symbol
        if is_actual:
            display = f" {self.SYMBOL_ACTUAL} "
            status_color = self._get_status_color(status)
            style = f"{status_color} on {bg_color}" if bg_color else status_color
            return display, style

        # Layer 1: Show hours (for planned or deadline without actual)
        if hours > 0:
            # Format: "4  " or "2.5" (right-aligned, 3 chars)
            display = f"{int(hours):2d} " if hours == int(hours) else f"{hours:3.1f}"
        else:
            display = self.SYMBOL_EMPTY  # No hours allocated: " · "

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
        if weekday == 5:  # Saturday
            return self.BACKGROUND_COLOR_SATURDAY
        elif weekday == 6:  # Sunday
            return self.BACKGROUND_COLOR_SUNDAY
        else:
            return self.BACKGROUND_COLOR

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
        legend.append("   ", style=f"on {self.BACKGROUND_COLOR}")
        legend.append(" Planned  ", style="dim")
        legend.append(self.SYMBOL_ACTUAL, style="bold blue")
        legend.append(" Actual (IN_PROGRESS)  ", style="dim")
        legend.append(self.SYMBOL_ACTUAL, style="bold green")
        legend.append(" Actual (COMPLETED)  ", style="dim")
        legend.append("   ", style=f"on {self.BACKGROUND_COLOR_DEADLINE}")
        legend.append(" Deadline  ", style="dim")
        legend.append("●", style="bold yellow")
        legend.append(" Today  ", style="dim")
        legend.append("   ", style=f"on {self.BACKGROUND_COLOR_SATURDAY}")
        legend.append(" Saturday  ", style="dim")
        legend.append("   ", style=f"on {self.BACKGROUND_COLOR_SUNDAY}")
        legend.append(" Sunday", style="dim")
        return legend

    def _build_workload_summary_row(
        self, tasks: list[Task], start_date: date, end_date: date
    ) -> Text:
        """Build workload summary timeline showing daily total hours.

        Args:
            tasks: List of all tasks
            start_date: Start date of the chart
            end_date: End date of the chart

        Returns:
            Rich Text object with workload summary
        """
        daily_workload = self.workload_calculator.calculate_daily_workload(
            tasks, start_date, end_date
        )
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
            elif hours <= 6.0:
                style = "bold green"
            elif hours <= 8.0:
                style = "bold yellow"
            else:
                style = "bold red"

            timeline.append(display, style=style)

        return timeline
