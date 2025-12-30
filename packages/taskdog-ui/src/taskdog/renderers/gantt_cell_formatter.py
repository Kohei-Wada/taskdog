"""Common formatting logic for Gantt chart rendering.

This module provides shared formatting utilities used by both CLI and TUI
Gantt chart implementations, eliminating code duplication and ensuring
consistent visualization across different interfaces.
"""

import math
from datetime import date, timedelta
from enum import Enum
from typing import Any

from rich.text import Text

from taskdog.constants.colors import (
    DAY_STYLE_SATURDAY,
    DAY_STYLE_SUNDAY,
    DAY_STYLE_WEEKDAY,
    STATUS_COLORS_BOLD,
)
from taskdog.constants.symbols import (
    BACKGROUND_COLOR,
    BACKGROUND_COLOR_DEADLINE,
    BACKGROUND_COLOR_HOLIDAY,
    BACKGROUND_COLOR_PLANNED_LIGHT,
    BACKGROUND_COLOR_SATURDAY,
    BACKGROUND_COLOR_SUNDAY,
    SYMBOL_CANCELED,
    SYMBOL_COMPLETED,
    SYMBOL_EMPTY,
    SYMBOL_IN_PROGRESS,
    SYMBOL_PENDING,
    SYMBOL_TODAY,
)
from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.shared.constants import (
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
        parsed_dates: dict[str, Any],
        status: TaskStatus,
        holidays: set[date],
    ) -> tuple[str, str]:
        """Format a single timeline cell with daily hours and styling.

        Args:
            current_date: Date of the cell
            hours: Allocated hours for this date
            parsed_dates: Dictionary of parsed task dates (from parse_task_dates)
            status: Task status
            holidays: Set of holiday dates for background coloring

        Returns:
            Tuple of (display_text, style_string)
        """
        # Determine which periods this date falls into
        is_planned = GanttCellFormatter._is_in_date_range(
            current_date, parsed_dates["planned_start"], parsed_dates["planned_end"]
        )
        is_actual = GanttCellFormatter._is_in_actual_period(current_date, parsed_dates)
        is_deadline = (
            parsed_dates["deadline"] and current_date == parsed_dates["deadline"]
        )

        # Determine background color
        bg_color = GanttCellFormatter._determine_cell_background_color(
            current_date, hours, is_planned, is_deadline, status, holidays
        )

        # Actual period (highest priority): show status symbol
        if is_actual:
            symbol = GanttCellFormatter.get_status_symbol(status)
            display = f" {symbol} "
            status_color = GanttCellFormatter.get_status_color(status)
            style = f"{status_color} on {bg_color}" if bg_color else status_color
            return display, style

        # Planned period or deadline: show hours
        display = GanttCellFormatter._format_hours_display(hours, status)
        style = f"on {bg_color}" if bg_color else "dim"

        return display, style

    @staticmethod
    def build_date_header_lines(
        start_date: date,
        end_date: date,
        holidays: set[date],
    ) -> tuple[Text, Text, Text]:
        """Build date header lines (Month, Today marker, Day) for the timeline.

        Args:
            start_date: Start date of the chart
            end_date: End date of the chart
            holidays: Set of holiday dates for day styling

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
            if current_date in holidays:
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
        legend.append("   ", style=f"on {BACKGROUND_COLOR_PLANNED_LIGHT}")
        legend.append(" Planned period  ", style="dim")
        legend.append("   ", style=f"on {BACKGROUND_COLOR}")
        legend.append(" Allocated hours  ", style="dim")
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
    def parse_task_dates(task: Task) -> dict[str, Any]:
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
    def get_status_color(status: TaskStatus | str) -> str:
        """Get color for task status.

        Args:
            status: Task status (enum or string)

        Returns:
            Color string with bold modifier
        """
        # Handle both TaskStatus enum and string values
        status_key = status.value if isinstance(status, Enum) else status
        return STATUS_COLORS_BOLD.get(status_key, "white")

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
    def _is_in_date_range(
        current_date: date, start: date | None, end: date | None
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

    @staticmethod
    def _is_in_actual_period(current_date: date, parsed_dates: dict[str, Any]) -> bool:
        """Check if a date is in the actual execution period.

        Handles three cases:
        1. IN_PROGRESS: actual_start exists, actual_end is None (show from start to today)
        2. COMPLETED/CANCELED: both actual_start and actual_end exist (show the range)
        3. CANCELED without start: only actual_end exists (show only end date)

        Args:
            current_date: Date to check
            parsed_dates: Dictionary of parsed task dates

        Returns:
            True if current_date is in actual period
        """
        actual_start = parsed_dates["actual_start"]
        actual_end = parsed_dates["actual_end"]

        if actual_start and not actual_end:
            # Case 1: IN_PROGRESS - show from actual_start to today
            today = date.today()
            return bool(actual_start <= current_date <= today)
        elif actual_start and actual_end:
            # Case 2: Both dates exist - show the complete range
            return bool(actual_start <= current_date <= actual_end)
        elif actual_end and not actual_start:
            # Case 3: Only actual_end (CANCELED without starting)
            return bool(current_date == actual_end)
        else:
            return False

    @staticmethod
    def _determine_cell_background_color(
        current_date: date,
        hours: float,
        is_planned: bool,
        is_deadline: bool,
        status: TaskStatus,
        holidays: set[date],
    ) -> str | None:
        """Determine background color for a timeline cell.

        Priority (highest to lowest):
        1. Deadline: Orange
        2. Allocated hours (for non-finished tasks): Darker color
        3. Planned period without allocation: Light gray

        Args:
            current_date: Date of the cell
            hours: Allocated hours for this date
            is_planned: Whether this date is in the planned period
            is_deadline: Whether this date is the deadline
            status: Task status
            holidays: Set of holiday dates

        Returns:
            Background color string or None
        """
        if is_deadline:
            return BACKGROUND_COLOR_DEADLINE

        # Finished tasks: no background color
        if status in [TaskStatus.COMPLETED, TaskStatus.CANCELED]:
            return None

        weekday = current_date.weekday()
        is_weekend_or_holiday = current_date in holidays or weekday in (
            SATURDAY,
            SUNDAY,
        )

        # Allocated hours: show darker color (takes priority over planned period)
        if hours > 0:
            if is_weekend_or_holiday:
                return GanttCellFormatter._get_weekend_holiday_background_color(
                    current_date, holidays
                )
            return BACKGROUND_COLOR

        # Planned period without allocation: show light color
        if is_planned:
            if is_weekend_or_holiday:
                return GanttCellFormatter._get_weekend_holiday_background_color(
                    current_date, holidays
                )
            return BACKGROUND_COLOR_PLANNED_LIGHT

        return None

    @staticmethod
    def _format_hours_display(hours: float, status: TaskStatus) -> str:
        """Format hours display for a timeline cell.

        Args:
            hours: Allocated hours for this date
            status: Task status

        Returns:
            Formatted display string (right-aligned, 3 characters)
        """
        # Hide planned hours for finished tasks
        if status in [TaskStatus.COMPLETED, TaskStatus.CANCELED]:
            return SYMBOL_EMPTY

        if hours > 0:
            # Format: "4  " or "2.5" (right-aligned, 3 chars)
            return f"{int(hours):2d} " if hours == int(hours) else f"{hours:3.1f}"
        else:
            return SYMBOL_EMPTY

    @staticmethod
    def _get_weekend_holiday_background_color(
        current_date: date,
        holidays: set[date],
    ) -> str:
        """Get background color for weekends and holidays.

        Used for weekends/holidays in the planned period.
        Priority: Holiday > Sunday > Saturday

        Args:
            current_date: Date to check
            holidays: Set of holiday dates

        Returns:
            Background color string (RGB) for weekend/holiday
        """
        # Check holiday first (highest priority)
        if current_date in holidays:
            return BACKGROUND_COLOR_HOLIDAY

        # Then check weekends
        weekday = current_date.weekday()
        if weekday == SATURDAY:
            return BACKGROUND_COLOR_SATURDAY
        elif weekday == SUNDAY:
            return BACKGROUND_COLOR_SUNDAY
        else:
            # Should not reach here (this method is only called for weekends/holidays)
            return BACKGROUND_COLOR
