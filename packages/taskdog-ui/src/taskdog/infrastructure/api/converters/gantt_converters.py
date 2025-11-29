"""Gantt chart data converters."""

from datetime import datetime
from typing import Any

from taskdog_core.application.dto.gantt_output import GanttDateRange, GanttOutput
from taskdog_core.application.dto.task_dto import GanttTaskDto
from taskdog_core.domain.entities.task import TaskStatus

from .datetime_utils import _parse_datetime_fields


def convert_to_gantt_output(data: dict[str, Any]) -> GanttOutput:
    """Convert API response to GanttOutput.

    Args:
        data: API response data

    Returns:
        GanttOutput with Gantt chart data
    """
    # Convert date_range
    date_range = GanttDateRange(
        start_date=datetime.fromisoformat(data["date_range"]["start_date"]).date(),
        end_date=datetime.fromisoformat(data["date_range"]["end_date"]).date(),
    )

    # Convert tasks (list[GanttTaskResponse] -> list[GanttTaskDto])
    tasks = []
    for task in data["tasks"]:
        # Parse datetime fields using utility
        dt_fields = _parse_datetime_fields(
            task,
            ["planned_start", "planned_end", "actual_start", "actual_end", "deadline"],
        )

        tasks.append(
            GanttTaskDto(
                id=task["id"],
                name=task["name"],
                status=TaskStatus[task["status"].upper()],
                estimated_duration=task.get("estimated_duration"),
                planned_start=dt_fields["planned_start"],
                planned_end=dt_fields["planned_end"],
                actual_start=dt_fields["actual_start"],
                actual_end=dt_fields["actual_end"],
                deadline=dt_fields["deadline"],
                is_finished=task["status"].upper() in ["COMPLETED", "CANCELED"],
            )
        )

    # Convert task_daily_hours: dict[str, dict[str, float]] -> dict[int, dict[date, float]]
    task_daily_hours = {
        int(task_id): {
            datetime.fromisoformat(date_str).date(): hours
            for date_str, hours in daily_hours.items()
        }
        for task_id, daily_hours in data["task_daily_hours"].items()
    }

    # Convert daily_workload: dict[str, float] -> dict[date, float]
    daily_workload = {
        datetime.fromisoformat(date_str).date(): hours
        for date_str, hours in data["daily_workload"].items()
    }

    # Convert holidays: list[str] -> set[date]
    holidays = {
        datetime.fromisoformat(date_str).date() for date_str in data["holidays"]
    }

    return GanttOutput(
        date_range=date_range,
        tasks=tasks,
        task_daily_hours=task_daily_hours,
        daily_workload=daily_workload,
        holidays=holidays,
        total_estimated_duration=data.get("total_estimated_duration", 0.0),
    )
