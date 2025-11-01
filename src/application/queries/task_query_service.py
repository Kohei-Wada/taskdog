"""Task query service for read-optimized operations."""

from datetime import date

from application.dto.gantt_output import GanttDateRange, GanttOutput
from application.dto.task_dto import GanttTaskDto, TaskRowDto
from application.queries.base import QueryService
from application.queries.filters.task_filter import TaskFilter
from application.queries.workload_calculator import WorkloadCalculator
from application.sorters.task_sorter import TaskSorter
from domain.entities.task import Task


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

    def get_filtered_tasks_as_dtos(
        self,
        filter_obj: TaskFilter | None = None,
        sort_by: str = "id",
        reverse: bool = False,
    ) -> list[TaskRowDto]:
        """Get filtered tasks as TaskRowDto list.

        Args:
            filter_obj: Optional filter to apply
            sort_by: Sort key
            reverse: Reverse sort order

        Returns:
            List of TaskRowDto
        """
        tasks = self.get_filtered_tasks(filter_obj, sort_by, reverse)
        return [self._task_to_row_dto(task) for task in tasks]

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

    def filter_by_tags(self, tags: list[str], match_all: bool = False) -> list[Task]:
        """Get tasks that match the specified tags.

        Args:
            tags: List of tags to filter by
            match_all: If True, task must have all tags (AND logic).
                      If False, task must have at least one tag (OR logic).

        Returns:
            List of tasks matching the tag filter
        """
        tasks = self.repository.get_all()

        if not tags:
            return tasks

        if match_all:
            # AND logic: task must have all specified tags
            return [task for task in tasks if all(tag in task.tags for tag in tags)]
        else:
            # OR logic: task must have at least one specified tag
            return [task for task in tasks if any(tag in task.tags for tag in tags)]

    def get_all_tags(self) -> dict[str, int]:
        """Get all unique tags with their task counts.

        Returns:
            Dictionary mapping tag names to task counts
        """
        tasks = self.repository.get_all()
        tag_counts: dict[str, int] = {}

        for task in tasks:
            for tag in task.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        return tag_counts

    def get_gantt_data(
        self,
        filter_obj: TaskFilter | None = None,
        sort_by: str = "id",
        reverse: bool = False,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> GanttOutput:
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
            GanttOutput containing business data for Gantt visualization
        """
        # Get filtered and sorted tasks
        tasks = self.get_filtered_tasks(filter_obj, sort_by, reverse)

        if not tasks:
            # Return empty result with today's date range
            today = date.today()
            return GanttOutput(
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
            task_dtos = [self._task_to_gantt_dto(task) for task in tasks]
            return GanttOutput(
                date_range=GanttDateRange(start_date=today, end_date=today),
                tasks=task_dtos,
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

        # Convert tasks to DTOs
        task_dtos = [self._task_to_gantt_dto(task) for task in tasks]

        return GanttOutput(
            date_range=GanttDateRange(start_date=range_start, end_date=range_end),
            tasks=task_dtos,
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
            for dt in [
                task.planned_start,
                task.planned_end,
                task.actual_start,
                task.actual_end,
                task.deadline,
            ]:
                if dt:
                    dates.append(dt.date())

        if not dates:
            return None

        # Calculate min/max from tasks
        auto_start = min(dates)
        auto_end = max(dates)

        # Use provided dates if available, otherwise use auto-calculated
        final_start = start_date if start_date else auto_start
        final_end = end_date if end_date else auto_end

        return final_start, final_end

    def _task_to_gantt_dto(self, task: Task) -> GanttTaskDto:
        """Convert Task entity to GanttTaskDto.

        Args:
            task: Task entity

        Returns:
            GanttTaskDto with fields needed for Gantt visualization
        """
        return GanttTaskDto(
            id=task.id,
            name=task.name,
            status=task.status,
            estimated_duration=task.estimated_duration,
            planned_start=task.planned_start,
            planned_end=task.planned_end,
            actual_start=task.actual_start,
            actual_end=task.actual_end,
            deadline=task.deadline,
            is_finished=task.is_finished,
        )

    def _task_to_row_dto(self, task: Task) -> TaskRowDto:
        """Convert Task entity to TaskRowDto.

        Args:
            task: Task entity

        Returns:
            TaskRowDto with fields needed for table display
        """
        # Tasks from repository must have an ID
        if task.id is None:
            raise ValueError("Task must have an ID")

        return TaskRowDto(
            id=task.id,
            name=task.name,
            priority=task.priority,
            status=task.status,
            planned_start=task.planned_start,
            planned_end=task.planned_end,
            deadline=task.deadline,
            actual_start=task.actual_start,
            actual_end=task.actual_end,
            estimated_duration=task.estimated_duration,
            actual_duration_hours=task.actual_duration_hours,
            is_fixed=task.is_fixed,
            depends_on=task.depends_on,
            tags=task.tags,
            is_archived=task.is_archived,
            is_finished=task.is_finished,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
