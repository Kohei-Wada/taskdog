"""Task query service for read-optimized operations."""

from datetime import date, datetime

from application.dto.gantt_result import GanttDateRange, GanttResult
from application.queries.base import QueryService
from application.queries.filters.task_filter import TaskFilter
from application.sorters.task_sorter import TaskSorter
from domain.entities.task import Task
from domain.services.workload_calculator import WorkloadCalculator
from shared.constants.formats import DATETIME_FORMAT


class TaskQueryService(QueryService):
    """Query service for task read operations.

    Provides read-only operations with filtering, sorting, and other
    query-specific logic. Optimized for data retrieval without state modification.
    """

    def __init__(self, repository):
        """Initialize query service with repository.

        Args:
            repository: Task repository for data access
        """
        super().__init__(repository)
        self.sorter = TaskSorter()
        self.workload_calculator = WorkloadCalculator()

    def get_filtered_tasks(
        self,
        filter_obj: TaskFilter | None = None,
        sort_by: str = "id",
        reverse: bool = False,
    ) -> list[Task]:
        """Get tasks with optional filtering and sorting.

        Args:
            filter_obj: Optional filter object to apply. If None, returns all tasks.
            sort_by: Sort key (id, priority, deadline, name, status, planned_start)
            reverse: Reverse sort order (default: False)

        Returns:
            Filtered and sorted list of tasks
        """
        tasks = self.repository.get_all()

        # Apply filter if provided
        if filter_obj:
            tasks = filter_obj.filter(tasks)

        # Sort tasks
        return self.sorter.sort(tasks, sort_by, reverse)

    def get_gantt_data(
        self,
        filter_obj: TaskFilter | None = None,
        sort_by: str = "id",
        reverse: bool = False,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> GanttResult:
        """Get Gantt chart data with business logic pre-computed.

        This method handles business data processing:
        - Filtering and sorting tasks
        - Calculating date ranges
        - Computing daily workload allocations per task
        - Computing daily workload totals

        Presentation logic (colors, styles, display flags) is handled
        by the renderer layer.

        Args:
            filter_obj: Optional filter object to apply
            sort_by: Sort key (id, priority, deadline, name, status, planned_start)
            reverse: Reverse sort order (default: False)
            start_date: Optional start date (auto-calculated if not provided)
            end_date: Optional end date (auto-calculated if not provided)

        Returns:
            GanttResult containing business data for Gantt visualization
        """
        # Get filtered and sorted tasks
        tasks = self.get_filtered_tasks(filter_obj, sort_by, reverse)

        if not tasks:
            # Return empty result with today's date range
            today = date.today()
            return GanttResult(
                date_range=GanttDateRange(start_date=today, end_date=today),
                tasks=[],
                task_daily_hours={},
                daily_workload={},
            )

        # Calculate date range
        date_range = self._calculate_date_range(tasks, start_date, end_date)

        if date_range is None:
            # No dates available in tasks
            today = date.today()
            return GanttResult(
                date_range=GanttDateRange(start_date=today, end_date=today),
                tasks=tasks,
                task_daily_hours={},
                daily_workload={},
            )

        range_start, range_end = date_range

        # Calculate daily hours per task
        task_daily_hours: dict[int, dict[date, float]] = {}
        for task in tasks:
            daily_hours = self.workload_calculator.get_task_daily_hours(task)
            if daily_hours:
                task_daily_hours[task.id] = daily_hours

        # Calculate daily workload totals
        daily_workload = self.workload_calculator.calculate_daily_workload(
            tasks, range_start, range_end
        )

        return GanttResult(
            date_range=GanttDateRange(start_date=range_start, end_date=range_end),
            tasks=tasks,
            task_daily_hours=task_daily_hours,
            daily_workload=daily_workload,
        )

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
