"""Common formatting logic for Gantt chart rendering.

This module provides shared formatting utilities used by both CLI and TUI
Gantt chart implementations, eliminating code duplication and ensuring
consistent visualization across different interfaces.
"""

import math
from datetime import date, timedelta
from typing import TYPE_CHECKING

from rich.text import Text

from domain.entities.task import Task, TaskStatus

if TYPE_CHECKING:
    from shared.utils.holiday_checker import HolidayChecker
from presentation.constants.colors import (
    DAY_STYLE_SATURDAY,
    DAY_STYLE_SUNDAY,
    DAY_STYLE_WEEKDAY,
    STATUS_COLORS_BOLD,
)
from presentation.constants.symbols import (
    BACKGROUND_COLOR,
    BACKGROUND_COLOR_DEADLINE,
    BACKGROUND_COLOR_HOLIDAY,
    BACKGROUND_COLOR_SATURDAY,
    BACKGROUND_COLOR_SUNDAY,
    SYMBOL_CANCELED,
    SYMBOL_COMPLETED,
    SYMBOL_EMPTY,
    SYMBOL_IN_PROGRESS,
    SYMBOL_PENDING,
    SYMBOL_TODAY,
)
from shared.constants import (
    SATURDAY,
    SUNDAY,
    WORKLOAD_COMFORTABLE_HOURS,
    WORKLOAD_MODERATE_HOURS,
)


class GanttCellFormatter:
    """Formatter for Gantt chart cells and headers.

    This class provides static methods for formatting Gantt chart components
    that are shared between CLI (Rich Table) and TUI (Textual DataTable).
    All methods are stateless and return Rich Text objects or tuples.
    """

    @staticmethod
    def format_timeline_cell(
        current_date: date,
        hours: float,
        parsed_dates: dict,
        status: TaskStatus,
        holiday_checker: "HolidayChecker | None" = None,
    ) -> tuple[str, str]:
        """Format a single timeline cell with daily hours and styling.

        Args:
            current_date: Date of the cell
            hours: Allocated hours for this date
            parsed_dates: Dictionary of parsed task dates (from parse_task_dates)
            status: Task status

        Returns:
            Tuple of (display_text, style_string)
        """
        # Check if date is in special periods
        is_planned = GanttCellFormatter._is_in_date_range(
            current_date, parsed_dates["planned_start"], parsed_dates["planned_end"]
        )

        # For actual period: handle three cases
        # 1. IN_PROGRESS (actual_start exists, actual_end is None): show from actual_start to today
        # 2. COMPLETED/CANCELED (both actual_start and actual_end exist): show the range
        # 3. CANCELED without actual_start (only actual_end exists): show only actual_end date
        if parsed_dates["actual_start"] and not parsed_dates["actual_end"]:
            # Case 1: IN_PROGRESS
            today = date.today()
            is_actual = parsed_dates["actual_start"] <= current_date <= today
        elif parsed_dates["actual_start"] and parsed_dates["actual_end"]:
            # Case 2: Both dates exist
            is_actual = GanttCellFormatter._is_in_date_range(
                current_date, parsed_dates["actual_start"], parsed_dates["actual_end"]
            )
        elif parsed_dates["actual_end"] and not parsed_dates["actual_start"]:
            # Case 3: Only actual_end (CANCELED without starting)
            is_actual = current_date == parsed_dates["actual_end"]
        else:
            is_actual = False

        is_deadline = parsed_dates["deadline"] and current_date == parsed_dates["deadline"]

        # Determine background color
        if is_deadline:
            bg_color = BACKGROUND_COLOR_DEADLINE
        elif is_planned and status not in [TaskStatus.COMPLETED, TaskStatus.CANCELED]:
            bg_color = GanttCellFormatter._get_background_color(current_date, holiday_checker)
        else:
            bg_color = None

        # Layer 2: Actual period (highest priority) - use status-specific symbol
        if is_actual:
            symbol = GanttCellFormatter.get_status_symbol(status)
            display = f" {symbol} "
            status_color = GanttCellFormatter.get_status_color(status)
            style = f"{status_color} on {bg_color}" if bg_color else status_color
            return display, style

        # Layer 1: Show hours (for planned or deadline without actual)
        # COMPLETED/CANCELED tasks: hide planned hours
        if hours > 0 and status not in [TaskStatus.COMPLETED, TaskStatus.CANCELED]:
            # Format: "4  " or "2.5" (right-aligned, 3 chars)
            display = f"{int(hours):2d} " if hours == int(hours) else f"{hours:3.1f}"
        else:
            display = SYMBOL_EMPTY  # No hours allocated: " · "

        # Apply background color
        style = f"on {bg_color}" if bg_color else "dim"

        return display, style

    @staticmethod
    def build_date_header_lines(
        start_date: date,
        end_date: date,
        holiday_checker: "HolidayChecker | None" = None,
    ) -> tuple[Text, Text, Text]:
        """Build date header lines (Month, Today marker, Day) for the timeline.

        Args:
            start_date: Start date of the chart
            end_date: End date of the chart
            holiday_checker: Optional HolidayChecker for holiday detection

        Returns:
            Tuple of three Rich Text objects (month_line, today_line, day_line)
        """
        days = (end_date - start_date).days + 1

        # Build each line as Rich Text
        month_line = Text()
        today_line = Text()
        day_line = Text()

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
                month_line.append(month_str, style="bold yellow")
                current_month = month
            else:
                month_line.append("   ", style="dim")

            # Line 2: Show yellow circle marker for today
            if is_today:
                today_line.append(f" {SYMBOL_TODAY} ", style="bold yellow")
            else:
                today_line.append("   ", style="dim")

            # Line 3: Show day number with color based on weekday/holiday
            day_str = f"{day:2d} "  # Right-aligned, 2 digits + space

            # Check if holiday (highest priority)
            if holiday_checker and holiday_checker.is_holiday(current_date):
                day_style = "bold yellow"  # Orange-ish color for holidays
            elif weekday == SATURDAY:
                day_style = DAY_STYLE_SATURDAY
            elif weekday == SUNDAY:
                day_style = DAY_STYLE_SUNDAY
            else:  # Weekday
                day_style = DAY_STYLE_WEEKDAY
            day_line.append(day_str, style=day_style)

        return month_line, today_line, day_line

    @staticmethod
    def build_workload_timeline(
        daily_workload: dict[date, float], start_date: date, end_date: date
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

    @staticmethod
    def build_legend() -> Text:
        """Build the legend text for the Gantt chart.

        Returns:
            Rich Text object with legend
        """
        legend = Text()
        legend.append("Legend: ", style="bold yellow")
        legend.append("   ", style=f"on {BACKGROUND_COLOR}")
        legend.append(" Planned  ", style="dim")
        legend.append(SYMBOL_IN_PROGRESS, style="bold blue")
        legend.append(" IN_PROGRESS  ", style="dim")
        legend.append(SYMBOL_COMPLETED, style="bold green")
        legend.append(" COMPLETED  ", style="dim")
        legend.append(SYMBOL_CANCELED, style="bold red")
        legend.append(" CANCELED  ", style="dim")
        legend.append("   ", style=f"on {BACKGROUND_COLOR_DEADLINE}")
        legend.append(" Deadline  ", style="dim")
        legend.append(SYMBOL_TODAY, style="bold yellow")
        legend.append(" Today  ", style="dim")
        legend.append("   ", style=f"on {BACKGROUND_COLOR_HOLIDAY}")
        legend.append(" Holiday  ", style="dim")
        legend.append("   ", style=f"on {BACKGROUND_COLOR_SATURDAY}")
        legend.append(" Saturday  ", style="dim")
        legend.append("   ", style=f"on {BACKGROUND_COLOR_SUNDAY}")
        legend.append(" Sunday", style="dim")
        return legend

    @staticmethod
    def parse_task_dates(task: Task) -> dict:
        """Parse all task dates into a dictionary.

        Args:
            task: Task to parse dates from

        Returns:
            Dictionary with parsed dates (planned_start, planned_end, actual_start,
            actual_end, deadline)
        """
        return {
            "planned_start": task.planned_start.date() if task.planned_start else None,
            "planned_end": task.planned_end.date() if task.planned_end else None,
            "actual_start": task.actual_start.date() if task.actual_start else None,
            "actual_end": task.actual_end.date() if task.actual_end else None,
            "deadline": task.deadline.date() if task.deadline else None,
        }

    @staticmethod
    def get_status_color(status: TaskStatus) -> str:
        """Get color for task status.

        Args:
            status: Task status

        Returns:
            Color string with bold modifier
        """
        # Use str(status) to handle both TaskStatus enum and string values
        return STATUS_COLORS_BOLD.get(status, "white")

    @staticmethod
    def get_status_symbol(status: TaskStatus) -> str:
        """Get symbol for task status in actual period.

        Args:
            status: Task status

        Returns:
            Single-character symbol representing the status
        """
        if status == TaskStatus.IN_PROGRESS:
            return SYMBOL_IN_PROGRESS
        elif status == TaskStatus.COMPLETED:
            return SYMBOL_COMPLETED
        elif status == TaskStatus.CANCELED:
            return SYMBOL_CANCELED
        else:  # PENDING (should not appear in actual period normally)
            return SYMBOL_PENDING

    @staticmethod
    def _is_in_date_range(current_date: date, start: date | None, end: date | None) -> bool:
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

    @staticmethod
    def _get_background_color(
        current_date: date,
        holiday_checker: "HolidayChecker | None" = None,
    ) -> str:
        """Get background color based on day of week and holidays.

        Priority: Holiday > Sunday > Saturday > Weekday

        Args:
            current_date: Date to check
            holiday_checker: Optional HolidayChecker for holiday detection

        Returns:
            Background color string (RGB)
        """
        # Check holiday first (highest priority after deadline)
        if holiday_checker and holiday_checker.is_holiday(current_date):
            return BACKGROUND_COLOR_HOLIDAY

        # Then check weekends
        weekday = current_date.weekday()
        if weekday == SATURDAY:
            return BACKGROUND_COLOR_SATURDAY
        elif weekday == SUNDAY:
            return BACKGROUND_COLOR_SUNDAY
        else:
            return BACKGROUND_COLOR
