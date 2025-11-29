"""Use case for getting Gantt chart data."""

from typing import TYPE_CHECKING

from taskdog_core.application.dto.gantt_output import GanttOutput
from taskdog_core.application.dto.query_inputs import GetGanttDataInput
from taskdog_core.application.queries.task_filter_builder import TaskFilterBuilder
from taskdog_core.application.use_cases.base import UseCase

if TYPE_CHECKING:
    from taskdog_core.application.queries.task_query_service import TaskQueryService
    from taskdog_core.domain.services.holiday_checker import IHolidayChecker


class GetGanttDataUseCase(UseCase[GetGanttDataInput, GanttOutput]):
    """Use case for getting Gantt chart data.

    This use case encapsulates the business logic for querying Gantt chart data,
    including filter construction, date range calculation, and workload computation.

    It follows the same pattern as write use cases (CreateTaskUseCase, etc.)
    but is optimized for read operations and Gantt-specific data processing.
    """

    def __init__(
        self,
        query_service: "TaskQueryService",
        holiday_checker: "IHolidayChecker | None" = None,
    ):
        """Initialize use case with dependencies.

        Args:
            query_service: Query service for filtering, sorting, and Gantt data
            holiday_checker: Optional holiday checker for workload calculation
        """
        self.query_service = query_service
        self.holiday_checker = holiday_checker
        self.filter_builder = TaskFilterBuilder()

    def execute(self, input_dto: GetGanttDataInput) -> GanttOutput:
        """Execute the Gantt data query.

        Builds filters from the input DTO, executes the query via
        TaskQueryService, and returns the complete Gantt chart data.

        Args:
            input_dto: Query parameters (filters, sorting, chart date range)

        Returns:
            GanttOutput with tasks, daily hours, workload, and holidays
        """
        # Build filter from input DTO
        filter_obj = self.filter_builder.build(input_dto)

        # Execute Gantt data query
        return self.query_service.get_gantt_data(
            filter_obj=filter_obj,
            sort_by=input_dto.sort_by,
            reverse=input_dto.reverse,
            start_date=input_dto.chart_start_date,
            end_date=input_dto.chart_end_date,
            holiday_checker=self.holiday_checker,
        )
