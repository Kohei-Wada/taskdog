"""Simulation endpoints for virtual task scheduling."""

from fastapi import APIRouter, HTTPException, status

from taskdog_core.application.dto.simulate_task_request import (
    SimulateTaskRequest as SimulateTaskRequestDto,
)
from taskdog_core.domain.exceptions.task_exceptions import TaskValidationError
from taskdog_server.api.dependencies import SimulateUseCaseDep
from taskdog_server.api.models.requests import SimulateTaskRequest
from taskdog_server.api.models.responses import SimulationResponse

router = APIRouter()


@router.post("/simulate", response_model=SimulationResponse)
async def simulate_task(
    request: SimulateTaskRequest,
    use_case: SimulateUseCaseDep,
) -> SimulationResponse:
    """Simulate a virtual task without saving to database.

    System automatically tries all 9 algorithms and returns the best result
    (earliest completion date). This helps users understand if their virtual
    task can be scheduled and when it would be completed.

    Args:
        request: Simulation parameters including virtual task details
        use_case: SimulateTaskScheduleUseCase dependency

    Returns:
        SimulationResponse with schedule prediction and workload analysis

    Raises:
        HTTPException: 400 if validation fails
    """
    try:
        # Convert Pydantic request to DTO
        dto = SimulateTaskRequestDto(
            estimated_duration=request.estimated_duration,
            name=request.name,
            priority=request.priority,
            deadline=request.deadline,
            depends_on=request.depends_on,
            tags=request.tags,
            is_fixed=request.is_fixed,
            max_hours_per_day=request.max_hours_per_day,
        )

        # Execute simulation
        result = use_case.execute(dto)

        # Convert date keys to ISO strings for JSON serialization
        daily_allocations_str = {
            date_obj.isoformat(): hours
            for date_obj, hours in result.daily_allocations.items()
        }

        # Build response
        return SimulationResponse(
            is_schedulable=result.is_schedulable,
            planned_start=result.planned_start,
            planned_end=result.planned_end,
            failure_reason=result.failure_reason,
            daily_allocations=daily_allocations_str,
            peak_workload=result.peak_workload,
            peak_date=result.peak_date,
            average_workload=result.average_workload,
            total_workload_days=result.total_workload_days,
            virtual_task_name=result.virtual_task_name,
            estimated_duration=result.estimated_duration,
            priority=result.priority,
            deadline=result.deadline,
            best_algorithm=result.best_algorithm,
            successful_algorithms=result.successful_algorithms,
            total_algorithms_tested=result.total_algorithms_tested,
        )

    except TaskValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {e}",
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {e}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation failed: {e}",
        ) from e
