"""Task query service for read-optimized operations."""

from datetime import date, timedelta
from typing import TYPE_CHECKING, Any

from taskdog_core.application.dto.gantt_output import GanttDateRange, GanttOutput
from taskdog_core.application.dto.task_dto import GanttTaskDto, TaskRowDto
from taskdog_core.application.queries.base import QueryService
from taskdog_core.application.queries.filters.task_filter import TaskFilter
from taskdog_core.application.queries.workload_calculator import WorkloadCalculator
from taskdog_core.application.sorters.task_sorter import TaskSorter
from taskdog_core.domain.entities.task import Task
from taskdog_core.domain.repositories.task_repository import TaskRepository

if TYPE_CHECKING:
    from taskdog_core.application.queries.filters.composite_filter import (
        CompositeFilter,
    )
    from taskdog_core.application.queries.filters.date_range_filter import (
        DateRangeFilter,
    )
    from taskdog_core.application.queries.filters.status_filter import StatusFilter
    from taskdog_core.application.queries.filters.tag_filter import TagFilter
    from taskdog_core.domain.services.holiday_checker import IHolidayChecker


class TaskQueryService(QueryService):
    """Query service for task read operations.

    Provides read-only operations with filtering, sorting, and other
    query-specific logic. Optimized for data retrieval without state modification.
    """

    def __init__(self, repository: TaskRepository) -> None:
        """Initialize query service with repository.

        Args:
            repository: Task repository for data access
        """
        super().__init__(repository)
        self.sorter = TaskSorter()

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

        Hybrid approach: Simple filters (archived, status, tags, dates) are applied
        at the SQL level for performance. Complex filters (dependencies, JSON fields)
        are applied in Python after fetching.

        Args:
            filter_obj: Optional filter object to apply. If None, returns all tasks.
            sort_by: Sort key (id, priority, deadline, name, status, planned_start)
            reverse: Reverse sort order (default: False)

        Returns:
            Filtered and sorted list of tasks
        """
        # Hybrid approach: Use SQL filtering for simple filters
        # Extract SQL-compatible filter parameters
        sql_params = self._extract_sql_params(filter_obj)

        # Get remaining complex filters that need Python processing
        remaining_filter = self._get_remaining_filter(filter_obj)

        # Fetch tasks with SQL filtering (repository.get_filtered() may optimize)
        tasks = self.repository.get_filtered(**sql_params)

        # Apply remaining complex filters in Python (if any)
        if remaining_filter:
            tasks = remaining_filter.filter(tasks)

        # Sort tasks
        return self.sorter.sort(tasks, sort_by, reverse)

    def _extract_sql_params(self, filter_obj: TaskFilter | None) -> dict[str, Any]:
        """Extract SQL-compatible filter parameters from filter object.

        Walks through the filter chain and extracts parameters that can be
        handled by repository.get_filtered() at the SQL level.

        Args:
            filter_obj: Filter object to extract from

        Returns:
            Dictionary of SQL filter parameters
        """
        from taskdog_core.application.queries.filters.composite_filter import (
            CompositeFilter,
        )
        from taskdog_core.application.queries.filters.date_range_filter import (
            DateRangeFilter,
        )
        from taskdog_core.application.queries.filters.non_archived_filter import (
            NonArchivedFilter,
        )
        from taskdog_core.application.queries.filters.status_filter import StatusFilter
        from taskdog_core.application.queries.filters.tag_filter import TagFilter

        params = self._get_default_sql_params()

        if not filter_obj:
            return params

        # Walk through filter chain and dispatch to handlers
        current_filter = filter_obj
        while current_filter:
            if isinstance(current_filter, NonArchivedFilter):
                self._handle_non_archived_filter(params)
            elif isinstance(current_filter, StatusFilter):
                self._handle_status_filter(params, current_filter)
            elif isinstance(current_filter, TagFilter):
                self._handle_tag_filter(params, current_filter)
            elif isinstance(current_filter, DateRangeFilter):
                self._handle_date_range_filter(params, current_filter)
            elif isinstance(current_filter, CompositeFilter):
                self._handle_composite_filter(params, current_filter)

            # Move to next filter in chain
            current_filter = getattr(current_filter, "_next", None)  # type: ignore[assignment]

        return params

    def _get_default_sql_params(self) -> dict[str, Any]:
        """Get default SQL filter parameters.

        Returns:
            Dictionary with default values for all SQL parameters
        """
        return {
            "include_archived": True,
            "status": None,
            "tags": None,
            "match_all_tags": False,
            "start_date": None,
            "end_date": None,
        }

    def _handle_non_archived_filter(self, params: dict[str, Any]) -> None:
        """Handle NonArchivedFilter by setting include_archived to False.

        Args:
            params: SQL parameters dictionary to update
        """
        params["include_archived"] = False

    def _handle_status_filter(
        self, params: dict[str, Any], filter_obj: "StatusFilter"
    ) -> None:
        """Handle StatusFilter by extracting status value.

        Args:
            params: SQL parameters dictionary to update
            filter_obj: StatusFilter instance
        """
        params["status"] = filter_obj.status

    def _handle_tag_filter(
        self, params: dict[str, Any], filter_obj: "TagFilter"
    ) -> None:
        """Handle TagFilter by extracting tags and match_all flag.

        Args:
            params: SQL parameters dictionary to update
            filter_obj: TagFilter instance
        """
        params["tags"] = filter_obj.tags
        params["match_all_tags"] = filter_obj.match_all

    def _handle_date_range_filter(
        self, params: dict[str, Any], filter_obj: "DateRangeFilter"
    ) -> None:
        """Handle DateRangeFilter by extracting start_date and end_date.

        Args:
            params: SQL parameters dictionary to update
            filter_obj: DateRangeFilter instance
        """
        params["start_date"] = filter_obj.start_date
        params["end_date"] = filter_obj.end_date

    def _handle_composite_filter(
        self, params: dict[str, Any], filter_obj: "CompositeFilter"
    ) -> None:
        """Handle CompositeFilter by recursively processing sub-filters.

        Args:
            params: SQL parameters dictionary to update
            filter_obj: CompositeFilter instance
        """
        for sub_filter in filter_obj.filters:
            sub_params = self._extract_sql_params(sub_filter)
            self._merge_sql_params(params, sub_params)

    def _merge_sql_params(
        self, params: dict[str, Any], sub_params: dict[str, Any]
    ) -> None:
        """Merge sub-filter parameters into main parameters.

        Uses the following merge logic:
        - For include_archived: Use AND logic (False takes precedence)
        - For other fields: Prefer non-None values from sub_params

        Args:
            params: Main parameters dictionary to update
            sub_params: Sub-filter parameters to merge
        """
        for key, value in sub_params.items():
            if value is not None and (params[key] is None or key == "include_archived"):
                if key == "include_archived":
                    # For archived, use AND logic (False takes precedence)
                    params[key] = params[key] and value
                else:
                    params[key] = value

    def _get_remaining_filter(self, filter_obj: TaskFilter | None) -> TaskFilter | None:
        """Get filters that cannot be handled by SQL and need Python processing.

        Some filters like TodayFilter have complex logic that cannot be easily
        translated to SQL WHERE clauses and need to be applied in Python.

        Args:
            filter_obj: Original filter object

        Returns:
            Filter object with only complex filters, or None if all filters are SQL-compatible
        """
        from taskdog_core.application.queries.filters.composite_filter import (
            CompositeFilter,
        )
        from taskdog_core.application.queries.filters.incomplete_filter import (
            IncompleteFilter,
        )
        from taskdog_core.application.queries.filters.this_week_filter import (
            ThisWeekFilter,
        )
        from taskdog_core.application.queries.filters.today_filter import TodayFilter

        if not filter_obj:
            return None

        # Check if filter contains complex filters that need Python processing
        complex_filters = []

        current_filter = filter_obj
        while current_filter:
            if isinstance(
                current_filter, TodayFilter | ThisWeekFilter | IncompleteFilter
            ):
                # These filters have complex logic that needs Python processing
                # - TodayFilter checks IN_PROGRESS status in addition to dates
                # - IncompleteFilter uses task.is_finished property
                complex_filters.append(current_filter)
            elif isinstance(current_filter, CompositeFilter):
                # Check sub-filters in CompositeFilter
                for sub_filter in current_filter.filters:
                    remaining = self._get_remaining_filter(sub_filter)
                    if remaining:
                        complex_filters.append(remaining)  # type: ignore[arg-type]

            current_filter = getattr(current_filter, "_next", None)  # type: ignore[assignment]

        # If we have complex filters, compose them
        if complex_filters:
            if len(complex_filters) == 1:
                return complex_filters[0]
            else:
                return CompositeFilter(complex_filters)  # type: ignore[arg-type]

        return None

    def filter_by_tags(self, tags: list[str], match_all: bool = False) -> list[Task]:
        """Get tasks that match the specified tags.

        Phase 3 (Issue 228): Optimized to use SQL JOIN instead of loading
        all tasks into memory and filtering in Python.

        Args:
            tags: List of tags to filter by
            match_all: If True, task must have all tags (AND logic).
                      If False, task must have at least one tag (OR logic).

        Returns:
            List of tasks matching the tag filter
        """
        if not tags:
            return self.repository.get_all()

        # Phase 3: Use SQL-based filtering
        # Check if repository has the optimized method
        if hasattr(self.repository, "get_task_ids_by_tags"):
            task_ids = self.repository.get_task_ids_by_tags(tags, match_all)

            if not task_ids:
                return []

            # Fetch tasks efficiently using get_by_ids
            task_dict = self.repository.get_by_ids(task_ids)
            return list(task_dict.values())

        # Fallback to old implementation for repositories without optimization
        tasks = self.repository.get_all()

        if match_all:
            # AND logic: task must have all specified tags
            return [task for task in tasks if all(tag in task.tags for tag in tags)]
        else:
            # OR logic: task must have at least one specified tag
            return [task for task in tasks if any(tag in task.tags for tag in tags)]

    def get_all_tags(self) -> dict[str, int]:
        """Get all unique tags with their task counts.

        Phase 3 (Issue 228): Optimized to use SQL aggregation (COUNT + GROUP BY)
        instead of loading all tasks into memory and counting in Python.

        Returns:
            Dictionary mapping tag names to task counts
        """
        # Phase 3: Use SQL-based aggregation
        # Check if repository has the optimized method
        if hasattr(self.repository, "get_tag_counts"):
            return self.repository.get_tag_counts()  # type: ignore[no-any-return]

        # Fallback to old implementation for repositories without optimization
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
        holiday_checker: "IHolidayChecker | None" = None,
    ) -> GanttOutput:
        """Get Gantt chart data with business logic pre-computed.

        This method handles business data processing:
        - Filtering and sorting tasks
        - Calculating date ranges
        - Computing daily workload allocations per task
        - Computing daily workload totals
        - Pre-computing holiday dates in the range

        Presentation logic (colors, styles, display flags) is handled
        by the renderer layer.

        Args:
            filter_obj: Optional filter object to apply
            sort_by: Sort key (id, priority, deadline, name, status, planned_start)
            reverse: Reverse sort order (default: False)
            start_date: Optional start date (auto-calculated if not provided)
            end_date: Optional end date (auto-calculated if not provided)
            holiday_checker: Optional holiday checker for pre-computing holidays

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
                holidays=set(),
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
                holidays=set(),
            )

        range_start, range_end = date_range

        # Create workload calculator with holiday checker for this request
        # Use factory to get appropriate strategy for display context
        # ActualScheduleStrategy honors manually scheduled tasks while excluding weekends and holidays
        from taskdog_core.application.services.workload_calculation_strategy_factory import (
            WorkloadCalculationStrategyFactory,
        )

        workload_strategy = WorkloadCalculationStrategyFactory.create_for_display(
            holiday_checker
        )
        workload_calculator = WorkloadCalculator(workload_strategy)

        # Calculate daily hours per task
        task_daily_hours: dict[int, dict[date, float]] = {}
        for task in tasks:
            daily_hours = workload_calculator.get_task_daily_hours(task)
            if daily_hours:
                assert task.id is not None, "Task must have ID (persisted entities)"
                task_daily_hours[task.id] = daily_hours

        # Calculate daily workload totals
        daily_workload = workload_calculator.calculate_daily_workload(
            tasks, range_start, range_end
        )

        # Pre-compute holidays in the date range
        holidays: set[date] = set()
        if holiday_checker:
            current = range_start
            while current <= range_end:
                if holiday_checker.is_holiday(current):
                    holidays.add(current)
                current += timedelta(days=1)

        # Convert tasks to DTOs
        task_dtos = [self._task_to_gantt_dto(task) for task in tasks]

        # Calculate total estimated duration
        total_estimated = sum(
            task.estimated_duration
            for task in tasks
            if task.estimated_duration is not None
        )

        return GanttOutput(
            date_range=GanttDateRange(start_date=range_start, end_date=range_end),
            tasks=task_dtos,
            task_daily_hours=task_daily_hours,
            daily_workload=daily_workload,
            holidays=holidays,
            total_estimated_duration=total_estimated,
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
        assert task.id is not None, "Task must have ID (persisted entities)"
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
