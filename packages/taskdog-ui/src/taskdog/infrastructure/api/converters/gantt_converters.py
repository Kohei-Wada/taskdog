"""Gantt chart data converters."""

from datetime import date
from typing import Any

from taskdog_core.application.dto.gantt_output import GanttDateRange, GanttOutput
from taskdog_core.application.dto.task_dto import GanttTaskDto
from taskdog_core.domain.entities.task import TaskStatus
from taskdog_core.shared.utils.datetime_parser import parse_iso_date

from .datetime_utils import _parse_date_dict, _parse_date_set, _parse_datetime_fields
from .exceptions import ConversionError


def _parse_date_range(data: dict[str, Any]) -> GanttDateRange:
    """Parse date_range from API response.

    Args:
        data: API response data containing date_range

    Returns:
        GanttDateRange with parsed dates

    Raises:
        ConversionError: If date parsing fails
    """
    try:
        start_date = parse_iso_date(data["date_range"]["start_date"])
        end_date = parse_iso_date(data["date_range"]["end_date"])

        if start_date is None or end_date is None:
            raise ConversionError(
                "date_range start_date or end_date is missing",
                field="date_range",
                value=data["date_range"],
            )

        return GanttDateRange(start_date=start_date, end_date=end_date)
    except (ValueError, KeyError) as e:
        raise ConversionError(
            f"Failed to parse date_range: {e}",
            field="date_range",
            value=data.get("date_range"),
        ) from e


def _parse_gantt_tasks(data: dict[str, Any]) -> list[GanttTaskDto]:
    """Parse tasks from API response.

    Args:
        data: API response data containing tasks

    Returns:
        List of GanttTaskDto
    """
    tasks = []
    for task in data["tasks"]:
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
    return tasks


def _parse_task_daily_hours(
    data: dict[str, Any],
) -> dict[int, dict[date, float]]:
    """Parse task_daily_hours from API response.

    Args:
        data: API response data containing task_daily_hours

    Returns:
        Dict mapping task_id to daily hours dict

    Raises:
        ConversionError: If date parsing fails
    """
    try:
        result: dict[int, dict[date, float]] = {}
        for task_id, daily_hours in data["task_daily_hours"].items():
            result[int(task_id)] = _parse_date_dict(
                {"daily_hours": daily_hours}, "daily_hours"
            )
        return result
    except (ValueError, KeyError) as e:
        raise ConversionError(
            f"Failed to parse task_daily_hours: {e}",
            field="task_daily_hours",
            value=data.get("task_daily_hours"),
        ) from e


def _parse_daily_workload(data: dict[str, Any]) -> dict[date, float]:
    """Parse daily_workload from API response.

    Args:
        data: API response data containing daily_workload

    Returns:
        Dict mapping date to hours

    Raises:
        ConversionError: If date parsing fails
    """
    return _parse_date_dict(data, "daily_workload")


def _parse_holidays(data: dict[str, Any]) -> set[date]:
    """Parse holidays from API response.

    Args:
        data: API response data containing holidays

    Returns:
        Set of holiday dates

    Raises:
        ConversionError: If date parsing fails
    """
    return _parse_date_set(data, "holidays")


def convert_to_gantt_output(data: dict[str, Any]) -> GanttOutput:
    """Convert API response to GanttOutput.

    Args:
        data: API response data

    Returns:
        GanttOutput with Gantt chart data

    Raises:
        ConversionError: If date parsing fails
    """
    return GanttOutput(
        date_range=_parse_date_range(data),
        tasks=_parse_gantt_tasks(data),
        task_daily_hours=_parse_task_daily_hours(data),
        daily_workload=_parse_daily_workload(data),
        holidays=_parse_holidays(data),
        total_estimated_duration=data.get("total_estimated_duration", 0.0),
    )
