from typing import List, Optional, Tuple
from datetime import datetime, date, timedelta
from rich.table import Table
from rich.console import Console
from rich.text import Text
from domain.entities.task import Task
from presentation.formatters.task_formatter import TaskFormatter
from presentation.formatters.constants import STATUS_STYLES, STATUS_COLORS_BOLD, DATETIME_FORMAT


class RichGanttFormatter(TaskFormatter):
    """Formats tasks as a Gantt chart using Rich."""

    # Visual constants for Gantt chart symbols
    SYMBOL_PLANNED = "░"
    SYMBOL_ACTUAL = "◆"
    SYMBOL_EMPTY = " · "
    SYMBOL_EMPTY_SPACE = "   "  # 3 spaces for planned background

    # Background colors
    BACKGROUND_COLOR = "rgb(100,100,100)"  # Weekday
    BACKGROUND_COLOR_SATURDAY = "rgb(100,100,150)"  # Saturday (blueish)
    BACKGROUND_COLOR_SUNDAY = "rgb(150,100,100)"  # Sunday (reddish)

    def __init__(self):
        self.console = Console()

    def format_tasks(
        self,
        tasks: List[Task],
        repository,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> str:
        """Format tasks into a Gantt chart with Rich.

        Args:
            tasks: List of all tasks
            repository: Repository instance for accessing task relationships
            start_date: Optional start date for the chart (overrides auto-calculation)
            end_date: Optional end date for the chart (overrides auto-calculation)

        Returns:
            Formatted string with Gantt chart
        """
        if not tasks:
            return "No tasks found."

        # Calculate date range for the chart
        date_range = self._calculate_date_range(tasks, start_date, end_date)

        if date_range is None:
            # No tasks with dates - just show task names
            return self._format_tasks_without_dates(tasks, repository)

        start_date, end_date = date_range
        days = (end_date - start_date).days + 1

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
        table.add_column("Timeline", style="white")

        # Add date header row
        date_header = self._build_date_header(start_date, end_date)
        table.add_row("", "[dim]Date[/dim]", date_header)

        # Get root tasks and render hierarchically
        root_tasks = [t for t in tasks if t.parent_id is None]
        for task in root_tasks:
            self._add_task_to_gantt(
                task, table, repository, start_date, end_date, depth=0
            )

        # Render to string with legend at bottom
        legend_text = self._build_legend()
        return self._render_to_string(table, legend_text)

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
        # Line 2: Day numbers
        line2 = Text()

        current_month = None
        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            month = current_date.month
            day = current_date.day

            # Line 1: Show month when it changes
            if month != current_month:
                month_str = current_date.strftime("%b")  # e.g., "Oct", "Nov"
                line1.append(month_str, style="bold yellow")
                # Pad the rest of the month's days
                current_month = month
            else:
                line1.append(" " * 3, style="dim")

            # Line 2: Show day number (always)
            day_str = f"{day:2d} "  # Right-aligned, 2 digits + space
            line2.append(day_str, style="cyan")

        # Combine both lines
        header = Text()
        header.append_text(line1)
        header.append("\n")
        header.append_text(line2)

        return header

    def _calculate_date_range(
        self,
        tasks: List[Task],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Optional[Tuple[date, date]]:
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

    def _format_tasks_without_dates(self, tasks: List[Task], repository) -> str:
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

        root_tasks = [t for t in tasks if t.parent_id is None]
        for task in root_tasks:
            self._add_simple_task(task, table, repository, depth=0)

        return self._render_to_string(table)

    def _add_simple_task(self, task: Task, table: Table, repository, depth: int):
        """Add task to simple table (no dates).

        Args:
            task: Task to add
            table: Rich Table object
            repository: Repository instance
            depth: Indentation depth
        """
        indent = "  " * depth
        task_name = f"{indent}{task.name}"

        status_style = self._get_status_style(task.status)
        status_text = f"[{status_style}]{task.status.value}[/{status_style}]"

        table.add_row(str(task.id), task_name, status_text)

        # Add children recursively
        children = repository.get_children(task.id)
        for child in children:
            self._add_simple_task(child, table, repository, depth + 1)

    def _add_task_to_gantt(
        self,
        task: Task,
        table: Table,
        repository,
        start_date: date,
        end_date: date,
        depth: int,
    ):
        """Add task to Gantt chart table recursively.

        Args:
            task: Task to add
            table: Rich Table object
            repository: Repository instance
            start_date: Start date of the chart
            end_date: End date of the chart
            depth: Indentation depth for hierarchy
        """
        indent = "  " * depth
        task_name = f"{indent}{task.name}"

        # Build timeline
        timeline = self._build_timeline(task, start_date, end_date)

        table.add_row(str(task.id), task_name, timeline)

        # Add children recursively
        children = repository.get_children(task.id)
        for child in children:
            self._add_task_to_gantt(
                child, table, repository, start_date, end_date, depth + 1
            )

    def _build_timeline(self, task: Task, start_date: date, end_date: date) -> Text:
        """Build timeline visualization for a task using layered approach.

        Args:
            task: Task to build timeline for
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

        # Build timeline with single loop applying layers in priority order
        timeline = Text()
        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)

            # Apply layers in priority order (highest priority last)
            # Layer 1: Base (empty day)
            symbol, style = self.SYMBOL_EMPTY, "dim"

            # Layer 2: Planned period (background only)
            layer_result = self._apply_planned_layer(current_date, parsed_dates)
            if layer_result:
                symbol, style = layer_result

            # Layer 3: Actual period (symbol + background)
            layer_result = self._apply_actual_layer(
                current_date, parsed_dates, task.status
            )
            if layer_result:
                symbol, style = layer_result

            # Layer 4: Deadline (highest priority)
            layer_result = self._apply_deadline_layer(current_date, parsed_dates)
            if layer_result:
                symbol, style = layer_result

            timeline.append(symbol, style=style)

        return timeline

    def _parse_task_dates(self, task: Task) -> dict:
        """Parse all task dates into a dictionary.

        Args:
            task: Task to parse dates from

        Returns:
            Dictionary with parsed dates (planned_start, planned_end, actual_start, actual_end, deadline)
        """
        return {
            "planned_start": self._parse_date(task.planned_start),
            "planned_end": self._parse_date(task.planned_end),
            "actual_start": self._parse_date(task.actual_start),
            "actual_end": self._parse_date(task.actual_end),
            "deadline": self._parse_date(task.deadline),
        }

    def _is_in_date_range(
        self, current_date: date, start: Optional[date], end: Optional[date]
    ) -> bool:
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

    def _apply_planned_layer(
        self, current_date: date, parsed_dates: dict
    ) -> Optional[Tuple[str, str]]:
        """Apply planned period styling.

        Args:
            current_date: Date to check
            parsed_dates: Dictionary of parsed task dates

        Returns:
            Tuple of (symbol, style) if date is in planned period, None otherwise
        """
        if self._is_in_date_range(
            current_date, parsed_dates["planned_start"], parsed_dates["planned_end"]
        ):
            bg_color = self._get_background_color(current_date)
            return (self.SYMBOL_EMPTY_SPACE, f"on {bg_color}")
        return None

    def _apply_actual_layer(
        self, current_date: date, parsed_dates: dict, status: str
    ) -> Optional[Tuple[str, str]]:
        """Apply actual period styling.

        Args:
            current_date: Date to check
            parsed_dates: Dictionary of parsed task dates
            status: Task status

        Returns:
            Tuple of (symbol, style) if date is in actual period, None otherwise
        """
        if self._is_in_date_range(
            current_date, parsed_dates["actual_start"], parsed_dates["actual_end"]
        ):
            status_color = self._get_status_color(status)
            bg_color = self._get_background_color(current_date)
            return (
                f" {self.SYMBOL_ACTUAL} ",
                f"{status_color} on {bg_color}",
            )
        return None

    def _apply_deadline_layer(
        self, current_date: date, parsed_dates: dict
    ) -> Optional[Tuple[str, str]]:
        """Apply deadline marker styling.

        Args:
            current_date: Date to check
            parsed_dates: Dictionary of parsed task dates

        Returns:
            Tuple of (symbol, style) if date is deadline, None otherwise
        """
        if parsed_dates["deadline"] and current_date == parsed_dates["deadline"]:
            return (f" {self.SYMBOL_ACTUAL} ", "bold red")
        return None

    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string to date object.

        Args:
            date_str: Date string in format YYYY-MM-DD HH:MM:SS

        Returns:
            date object or None
        """
        if not date_str:
            return None
        try:
            dt = datetime.strptime(date_str, DATETIME_FORMAT)
            return dt.date()
        except ValueError:
            return None

    def _get_status_style(self, status: str) -> str:
        """Get Rich style for a task status.

        Args:
            status: Task status

        Returns:
            Rich style string
        """
        return STATUS_STYLES.get(status, "white")

    def _get_status_color(self, status: str) -> str:
        """Get color for status bar in Gantt chart.

        Args:
            status: Task status

        Returns:
            Color string
        """
        return STATUS_COLORS_BOLD.get(status, "white")

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
        legend.append(self.SYMBOL_ACTUAL, style="bold red")
        legend.append(" Deadline  ", style="dim")
        legend.append("   ", style=f"on {self.BACKGROUND_COLOR_SATURDAY}")
        legend.append(" Saturday  ", style="dim")
        legend.append("   ", style=f"on {self.BACKGROUND_COLOR_SUNDAY}")
        legend.append(" Sunday", style="dim")
        return legend

    def _render_to_string(
        self, table: Table, footer: Optional[Text] = None, width: Optional[int] = None
    ) -> str:
        """Render a Rich table to string with optional footer.

        Args:
            table: Rich Table to render
            footer: Optional footer text to append after table
            width: Optional console width

        Returns:
            Rendered string
        """
        from io import StringIO

        string_io = StringIO()
        console_kwargs = {"file": string_io, "force_terminal": True}
        if width:
            console_kwargs["width"] = width

        console = Console(**console_kwargs)
        console.print(table)

        if footer:
            console.print()
            console.print(footer)

        return string_io.getvalue().rstrip()
