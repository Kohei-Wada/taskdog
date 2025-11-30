"""Optimization data converters."""

from datetime import date as date_type
from datetime import datetime
from typing import Any

from taskdog_core.application.dto.optimization_output import (
    OptimizationOutput,
    SchedulingFailure,
)
from taskdog_core.application.dto.optimization_summary import OptimizationSummary
from taskdog_core.application.dto.task_dto import TaskSummaryDto
from taskdog_core.shared.utils.datetime_parser import parse_iso_date

from .exceptions import ConversionError


def _parse_optimization_summary(
    summary_data: dict[str, Any], failures: list[dict[str, Any]]
) -> OptimizationSummary:
    """Parse optimization summary from API response.

    Args:
        summary_data: Summary section from API response
        failures: Failures list from API response

    Returns:
        OptimizationSummary object

    Raises:
        ConversionError: If date parsing fails
    """
    # Calculate days span from start_date and end_date
    try:
        start_date = parse_iso_date(summary_data["start_date"])
        end_date = parse_iso_date(summary_data["end_date"])

        if start_date is None or end_date is None:
            raise ConversionError(
                "start_date or end_date is missing in optimization summary",
                field="summary",
                value=summary_data,
            )

        days_span = (end_date - start_date).days + 1
    except (ValueError, KeyError) as e:
        raise ConversionError(
            f"Failed to parse optimization summary dates: {e}",
            field="summary",
            value=summary_data,
        ) from e

    # Create TaskSummaryDto objects for unscheduled tasks from failures
    unscheduled_tasks = [
        TaskSummaryDto(id=f["task_id"], name=f["task_name"]) for f in failures
    ]

    return OptimizationSummary(
        new_count=summary_data["scheduled_tasks"],
        rescheduled_count=0,  # API doesn't distinguish between new and rescheduled
        total_hours=summary_data["total_hours"],
        deadline_conflicts=0,  # Not provided by API
        days_span=days_span,
        unscheduled_tasks=unscheduled_tasks,
        overloaded_days=[],  # Not provided by API
    )


def _parse_scheduling_failures(
    failures_data: list[dict[str, Any]],
) -> list[SchedulingFailure]:
    """Parse scheduling failures from API response.

    Args:
        failures_data: Failures list from API response

    Returns:
        List of SchedulingFailure objects
    """
    return [
        SchedulingFailure(
            task=TaskSummaryDto(id=f["task_id"], name=f["task_name"]),
            reason=f["reason"],
        )
        for f in failures_data
    ]


def convert_to_optimization_output(data: dict[str, Any]) -> OptimizationOutput:
    """Convert API response to OptimizationOutput.

    Args:
        data: API response data with format:
            {
                "summary": {
                    "total_tasks": int,
                    "scheduled_tasks": int,
                    "failed_tasks": int,
                    "total_hours": float,
                    "start_date": str (ISO),
                    "end_date": str (ISO),
                    "algorithm": str
                },
                "failures": [{
                    "task_id": int,
                    "task_name": str,
                    "reason": str
                }],
                "message": str
            }

    Returns:
        OptimizationOutput with all optimization results
    """
    summary = _parse_optimization_summary(data["summary"], data["failures"])
    failures = _parse_scheduling_failures(data["failures"])

    # Note: API response doesn't include successful_tasks details
    # We'll create minimal TaskSummaryDto objects
    successful_count = data["summary"]["scheduled_tasks"]
    successful_tasks = [
        TaskSummaryDto(id=i, name=f"Task {i}") for i in range(successful_count)
    ]

    # Daily allocations and task states not provided in response
    daily_allocations: dict[date_type, float] = {}
    task_states_before: dict[int, datetime | None] = {}

    return OptimizationOutput(
        successful_tasks=successful_tasks,
        failed_tasks=failures,
        daily_allocations=daily_allocations,
        summary=summary,
        task_states_before=task_states_before,
    )
