"""Formatter for task table display."""

from datetime import datetime

from domain.entities.task import Task, TaskStatus


class TaskTableFormatter:
    """Formatter for task table cells.

    This class provides static methods to format task data for display
    in the task table widget.
    """

    @staticmethod
    def format_duration(task: Task) -> str:
        """Format duration information for display.

        Args:
            task: Task to format duration for

        Returns:
            Formatted duration string
        """
        if not task.estimated_duration and not task.actual_duration_hours:
            return "-"

        parts = []
        if task.estimated_duration:
            parts.append(f"E:{task.estimated_duration}h")
        if task.actual_duration_hours:
            parts.append(f"A:{task.actual_duration_hours}h")

        return " ".join(parts)

    @staticmethod
    def format_dependencies(task: Task) -> str:
        """Format task dependencies for display.

        Args:
            task: Task to extract dependencies from

        Returns:
            Formatted dependencies string (e.g., "1,2,3" or "-")
        """
        if not task.depends_on:
            return "-"
        return ",".join(str(dep_id) for dep_id in task.depends_on)

    @staticmethod
    def format_deadline(deadline: datetime | None) -> str:
        """Format deadline for display.

        Args:
            deadline: Deadline datetime object or None

        Returns:
            Formatted deadline string
        """
        if not deadline:
            return "-"

        # Show year only if different from current year
        current_year = datetime.now().year
        if deadline.year == current_year:
            # Current year: MM-DD HH:MM
            return deadline.strftime("%m-%d %H:%M")
        else:
            # Different year: 'YY MM-DD HH:MM
            return deadline.strftime("'%y %m-%d %H:%M")

    @staticmethod
    def format_estimated_duration(task: Task) -> str:
        """Format estimated duration for display.

        Args:
            task: Task to format estimated duration for

        Returns:
            Formatted estimated duration string (e.g., "5h" or "-")
        """
        if not task.estimated_duration:
            return "-"
        return f"{task.estimated_duration}h"

    @staticmethod
    def format_actual_duration(task: Task) -> str:
        """Format actual duration for display.

        Args:
            task: Task to format actual duration for

        Returns:
            Formatted actual duration string (e.g., "3h" or "-")
        """
        if not task.actual_duration_hours:
            return "-"
        return f"{task.actual_duration_hours}h"

    @staticmethod
    def format_planned_start(planned_start: datetime | None) -> str:
        """Format planned start datetime for display.

        Args:
            planned_start: Planned start datetime object or None

        Returns:
            Formatted planned start string
        """
        if not planned_start:
            return "-"

        # Show year only if different from current year
        current_year = datetime.now().year
        if planned_start.year == current_year:
            # Current year: MM-DD HH:MM
            return planned_start.strftime("%m-%d %H:%M")
        else:
            # Different year: 'YY MM-DD HH:MM
            return planned_start.strftime("'%y %m-%d %H:%M")

    @staticmethod
    def format_planned_end(planned_end: datetime | None) -> str:
        """Format planned end datetime for display.

        Args:
            planned_end: Planned end datetime object or None

        Returns:
            Formatted planned end string
        """
        if not planned_end:
            return "-"

        # Show year only if different from current year
        current_year = datetime.now().year
        if planned_end.year == current_year:
            # Current year: MM-DD HH:MM
            return planned_end.strftime("%m-%d %H:%M")
        else:
            # Different year: 'YY MM-DD HH:MM
            return planned_end.strftime("'%y %m-%d %H:%M")

    @staticmethod
    def format_actual_start(actual_start: datetime | None) -> str:
        """Format actual start datetime for display.

        Args:
            actual_start: Actual start datetime object or None

        Returns:
            Formatted actual start string
        """
        if not actual_start:
            return "-"

        # Show year only if different from current year
        current_year = datetime.now().year
        if actual_start.year == current_year:
            # Current year: MM-DD HH:MM
            return actual_start.strftime("%m-%d %H:%M")
        else:
            # Different year: 'YY MM-DD HH:MM
            return actual_start.strftime("'%y %m-%d %H:%M")

    @staticmethod
    def format_actual_end(actual_end: datetime | None) -> str:
        """Format actual end datetime for display.

        Args:
            actual_end: Actual end datetime object or None

        Returns:
            Formatted actual end string
        """
        if not actual_end:
            return "-"

        # Show year only if different from current year
        current_year = datetime.now().year
        if actual_end.year == current_year:
            # Current year: MM-DD HH:MM
            return actual_end.strftime("%m-%d %H:%M")
        else:
            # Different year: 'YY MM-DD HH:MM
            return actual_end.strftime("'%y %m-%d %H:%M")

    @staticmethod
    def format_elapsed_time(task: Task) -> str:
        """Format elapsed time for IN_PROGRESS tasks.

        Args:
            task: Task to format elapsed time for

        Returns:
            Formatted elapsed time string (e.g., "15:04:38" or "3d 15:04:38")
        """
        if task.status != TaskStatus.IN_PROGRESS or not task.actual_start:
            return "-"

        # Calculate elapsed time
        elapsed_seconds = int((datetime.now() - task.actual_start).total_seconds())

        # Convert to days, hours, minutes, seconds
        days = elapsed_seconds // 86400
        remaining_seconds = elapsed_seconds % 86400
        hours = remaining_seconds // 3600
        minutes = (remaining_seconds % 3600) // 60
        seconds = remaining_seconds % 60

        # Format based on duration
        if days > 0:
            return f"{days}d {hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
