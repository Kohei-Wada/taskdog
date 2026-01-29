"""Formatting logic for Timeline chart rendering.

This module provides formatting utilities for the Timeline chart,
which displays actual work times on a horizontal time axis.
"""

from datetime import time

from rich.text import Text

from taskdog.constants.colors import STATUS_COLORS_BOLD
from taskdog_core.domain.entities.task import TaskStatus

# Timeline constants
CHARS_PER_HOUR = 4  # Number of characters per hour in the timeline
TIMELINE_BAR_CHAR = "█"  # Full block character for work bars
TIMELINE_EMPTY_CHAR = " "  # Space for empty cells


class TimelineCellFormatter:
    """Formatter for Timeline chart cells and headers.

    This class provides static methods for formatting Timeline chart components.
    All methods are stateless and return Rich Text objects or tuples.
    """

    @staticmethod
    def build_hour_header(start_hour: int, end_hour: int) -> Text:
        """Build hour header row for the timeline.

        Args:
            start_hour: First hour to display (e.g., 8)
            end_hour: Last hour to display (e.g., 18)

        Returns:
            Rich Text object with hour labels
        """
        header = Text()
        for hour in range(start_hour, end_hour + 1):
            # Format: "08  " or "12  " (4 chars per hour)
            label = f"{hour:02d}  "
            header.append(label, style="dim")
        return header

    @staticmethod
    def build_timeline_bar(
        actual_start: time,
        actual_end: time,
        start_hour: int,
        end_hour: int,
        status: TaskStatus,
    ) -> Text:
        """Build a timeline bar showing work period.

        Args:
            actual_start: Start time of work
            actual_end: End time of work
            start_hour: Display start hour
            end_hour: Display end hour
            status: Task status for coloring

        Returns:
            Rich Text object with timeline bar
        """
        timeline = Text()
        total_chars = (end_hour - start_hour + 1) * CHARS_PER_HOUR
        bar_color = TimelineCellFormatter.get_status_color(status)

        # Calculate positions in character space
        start_minutes = actual_start.hour * 60 + actual_start.minute
        end_minutes = actual_end.hour * 60 + actual_end.minute
        display_start_minutes = start_hour * 60

        for char_idx in range(total_chars):
            # Calculate the time range this character represents
            char_start_minutes = display_start_minutes + (
                char_idx * 60 // CHARS_PER_HOUR
            )
            char_end_minutes = display_start_minutes + (
                (char_idx + 1) * 60 // CHARS_PER_HOUR
            )

            # Check if this character falls within the work period
            if char_start_minutes < end_minutes and char_end_minutes > start_minutes:
                timeline.append(TIMELINE_BAR_CHAR, style=bar_color)
            else:
                timeline.append(TIMELINE_EMPTY_CHAR, style="dim")

        return timeline

    @staticmethod
    def get_status_color(status: TaskStatus) -> str:
        """Get color for task status.

        Args:
            status: Task status

        Returns:
            Color string with bold modifier
        """
        status_key = status.value if hasattr(status, "value") else str(status)
        return STATUS_COLORS_BOLD.get(status_key, "white")

    @staticmethod
    def format_duration(hours: float) -> str:
        """Format duration for display.

        Args:
            hours: Duration in hours

        Returns:
            Formatted string (e.g., "2.5h", "1.0h")
        """
        return f"{hours:.1f}h"

    @staticmethod
    def build_legend() -> Text:
        """Build the legend text for the Timeline chart.

        Returns:
            Rich Text object with legend
        """
        legend = Text()
        legend.append("Legend: ", style="bold yellow")
        legend.append(TIMELINE_BAR_CHAR * 3, style="bold blue")
        legend.append(" IN_PROGRESS  ", style="dim")
        legend.append(TIMELINE_BAR_CHAR * 3, style="bold green")
        legend.append(" COMPLETED  ", style="dim")
        legend.append(TIMELINE_BAR_CHAR * 3, style="bold red")
        legend.append(" CANCELED", style="dim")
        return legend
