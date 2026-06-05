"""Gantt overlay data converters."""

from datetime import date
from typing import Any

from taskdog_core.application.dto.gantt_overlay import GanttDateRange, GanttOverlay
from taskdog_core.shared.utils.datetime_parser import parse_iso_date

from .datetime_utils import _parse_date_dict, _parse_date_set
from .exceptions import ConversionError, require_key


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
        date_range = require_key(data, "date_range")
        start_date = parse_iso_date(require_key(date_range, "start_date"))
        end_date = parse_iso_date(require_key(date_range, "end_date"))

        if start_date is None or end_date is None:
            raise ConversionError(
                "date_range start_date or end_date is missing",
                field="date_range",
                value=date_range,
            )

        return GanttDateRange(start_date=start_date, end_date=end_date)
    except (ValueError, KeyError) as e:
        raise ConversionError(
            f"Failed to parse date_range: {e}",
            field="date_range",
            value=data.get("date_range"),
        ) from e


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
        for task_id, daily_hours in require_key(data, "task_daily_hours").items():
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


def convert_to_gantt_overlay(data: dict[str, Any]) -> GanttOverlay:
    """Convert an API Gantt overlay payload to a GanttOverlay DTO.

    Args:
        data: API response data (the ``gantt`` overlay object)

    Returns:
        GanttOverlay with Gantt-specific data (no task fields)

    Raises:
        ConversionError: If date parsing fails
    """
    return GanttOverlay(
        date_range=_parse_date_range(data),
        task_daily_hours=_parse_task_daily_hours(data),
        daily_workload=_parse_daily_workload(data),
        holidays=_parse_holidays(data),
        total_estimated_duration=data.get("total_estimated_duration", 0.0),
    )
