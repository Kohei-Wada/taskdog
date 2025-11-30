"""Duration formatting utilities."""

from datetime import datetime

from taskdog.view_models.task_view_model import TaskRowViewModel
from taskdog_core.domain.entities.task import TaskStatus


class DurationFormatter:
    """Formats duration values for display in the UI."""

    @staticmethod
    def format_hours(hours: float | None) -> str:
        """Format hours as a string.

        Args:
            hours: Hours value or None

        Returns:
            Formatted string (e.g., "5") or "-" if None
        """
        if hours is None:
            return "-"
        return str(hours)

    @staticmethod
    def format_estimated_duration(task_vm: TaskRowViewModel) -> str:
        """Format estimated duration for display.

        Args:
            task_vm: TaskRowViewModel to format estimated duration for

        Returns:
            Formatted estimated duration string (e.g., "5" or "-")
        """
        return DurationFormatter.format_hours(task_vm.estimated_duration)

    @staticmethod
    def format_actual_duration(task_vm: TaskRowViewModel) -> str:
        """Format actual duration for display.

        Args:
            task_vm: TaskRowViewModel to format actual duration for

        Returns:
            Formatted actual duration string (e.g., "3" or "-")
        """
        return DurationFormatter.format_hours(task_vm.actual_duration_hours)

    @staticmethod
    def format_elapsed_time(task_vm: TaskRowViewModel) -> str:
        """Format elapsed time for IN_PROGRESS tasks.

        Args:
            task_vm: TaskRowViewModel to format elapsed time for

        Returns:
            Formatted elapsed time string (e.g., "15:04:38" or "3d 15:04:38")
        """
        if task_vm.status != TaskStatus.IN_PROGRESS or not task_vm.actual_start:
            return "-"

        # Calculate elapsed time
        elapsed_seconds = int((datetime.now() - task_vm.actual_start).total_seconds())

        # Convert to days, hours, minutes, seconds
        days = elapsed_seconds // 86400
        remaining_seconds = elapsed_seconds % 86400
        hours = remaining_seconds // 3600
        minutes = (remaining_seconds % 3600) // 60
        seconds = remaining_seconds % 60

        # Format based on duration
        if days > 0:
            return f"{days}d {hours}:{minutes:02d}:{seconds:02d}"
        return f"{hours}:{minutes:02d}:{seconds:02d}"
