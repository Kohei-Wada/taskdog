"""Presenter for converting TaskListOutput to TimelineViewModel.

This presenter filters tasks that have actual_start/actual_end on the target date
and creates presentation-ready view models for the Timeline chart.
"""

from datetime import date, datetime, time

from taskdog.view_models.timeline_view_model import (
    TimelineTaskRowViewModel,
    TimelineViewModel,
)
from taskdog_core.application.dto.task_dto import TaskRowDto
from taskdog_core.application.dto.task_list_output import TaskListOutput

# Default display hours
DEFAULT_START_HOUR = 8
DEFAULT_END_HOUR = 18
MIN_DISPLAY_HOURS = 2  # Minimum hours to show in timeline


class TimelinePresenter:
    """Presenter for converting TaskListOutput to TimelineViewModel.

    This class is responsible for:
    1. Filtering tasks that have actual work on the target date
    2. Calculating display time range
    3. Converting task data to presentation-ready ViewModels
    """

    def present(
        self, task_list: TaskListOutput, target_date: date
    ) -> TimelineViewModel:
        """Convert TaskListOutput to TimelineViewModel for a specific date.

        Args:
            task_list: Task list from the API
            target_date: The date to show timeline for

        Returns:
            TimelineViewModel with presentation-ready data
        """
        # Filter and convert tasks that have work on the target date
        rows: list[TimelineTaskRowViewModel] = []
        min_hour = DEFAULT_END_HOUR
        max_hour = DEFAULT_START_HOUR

        for task_row in task_list.tasks:
            row = self._try_convert_task(task_row, target_date)
            if row is not None:
                rows.append(row)
                # Track time range
                min_hour = min(min_hour, row.actual_start.hour)
                max_hour = max(max_hour, row.actual_end.hour)

        # Sort by actual_start (ascending)
        rows.sort(key=lambda r: (r.actual_start.hour, r.actual_start.minute))

        # Calculate display range
        if rows:
            start_hour = max(0, min_hour)
            end_hour = min(23, max_hour + 1)  # Include the end hour
        else:
            start_hour = DEFAULT_START_HOUR
            end_hour = DEFAULT_END_HOUR

        # Ensure minimum display width
        if end_hour - start_hour < MIN_DISPLAY_HOURS:
            end_hour = start_hour + MIN_DISPLAY_HOURS

        # Calculate totals
        total_work_hours = sum(row.duration_hours for row in rows)

        return TimelineViewModel(
            target_date=target_date,
            rows=rows,
            start_hour=start_hour,
            end_hour=end_hour,
            total_work_hours=total_work_hours,
            task_count=len(rows),
        )

    def _try_convert_task(
        self, task_row: TaskRowDto, target_date: date
    ) -> TimelineTaskRowViewModel | None:
        """Try to convert a TaskRowDto to TimelineTaskRowViewModel.

        Returns None if the task has no work on the target date.

        Args:
            task_row: Task row DTO from the API
            target_date: The date to check for work

        Returns:
            TimelineTaskRowViewModel if task has work on target_date, None otherwise
        """
        # Check if task has actual start/end on the target date
        actual_start = task_row.actual_start
        actual_end = task_row.actual_end

        if actual_start is None:
            return None

        # For IN_PROGRESS tasks, use "now" as end time if on target date
        if actual_end is None:
            if actual_start.date() == target_date:
                # Task started today and still in progress
                now = datetime.now()
                if now.date() == target_date:
                    actual_end = now
                else:
                    # Started today but we're looking at a past date?
                    # Use end of day
                    actual_end = datetime.combine(target_date, time(23, 59, 59))
            else:
                return None

        # Calculate the overlap with the target date
        start_time, end_time = self._get_work_times_on_date(
            actual_start, actual_end, target_date
        )

        if start_time is None or end_time is None:
            return None

        # Calculate duration on this date
        duration_hours = self._calculate_duration_hours(start_time, end_time)

        if duration_hours <= 0:
            return None

        # Use is_finished from DTO (consistent with other presenters)
        is_finished = task_row.is_finished

        # Apply strikethrough for finished tasks
        formatted_name = task_row.name
        if is_finished:
            formatted_name = f"[strike dim]{task_row.name}[/strike dim]"

        return TimelineTaskRowViewModel(
            task_id=task_row.id,
            name=task_row.name,
            formatted_name=formatted_name,
            actual_start=start_time,
            actual_end=end_time,
            duration_hours=duration_hours,
            status=task_row.status,
            is_finished=is_finished,
        )

    def _get_work_times_on_date(
        self, actual_start: datetime, actual_end: datetime, target_date: date
    ) -> tuple[time | None, time | None]:
        """Get the work start and end times for a specific date.

        Handles cases where work spans multiple days by clipping to the target date.

        Args:
            actual_start: Task actual start datetime
            actual_end: Task actual end datetime
            target_date: The date to get times for

        Returns:
            Tuple of (start_time, end_time) on target_date, or (None, None) if no overlap
        """
        start_date = actual_start.date()
        end_date = actual_end.date()

        # Check if target_date is within the work period
        if target_date < start_date or target_date > end_date:
            return None, None

        # Determine start time on target date
        # (Work continued from previous day uses midnight)
        start_time = actual_start.time() if target_date == start_date else time(0, 0)

        # Determine end time on target date
        # (Work continued to next day uses end of day)
        end_time = actual_end.time() if target_date == end_date else time(23, 59, 59)

        return start_time, end_time

    def _calculate_duration_hours(self, start_time: time, end_time: time) -> float:
        """Calculate duration in hours between two times.

        Args:
            start_time: Start time
            end_time: End time

        Returns:
            Duration in hours
        """
        start_minutes = start_time.hour * 60 + start_time.minute
        end_minutes = end_time.hour * 60 + end_time.minute

        duration_minutes = end_minutes - start_minutes
        return max(0, duration_minutes / 60.0)
