"""Shared serialization helpers for MCP tool responses."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from taskdog_core.shared.utils.datetime_parser import (
    parse_iso_datetime as core_parse_iso_datetime,
)

if TYPE_CHECKING:
    from datetime import datetime


def iso(dt: datetime | None) -> str | None:
    """ISO-format a datetime, or None."""
    return dt.isoformat() if dt else None


def model_dump(model: Any | None) -> dict[str, Any] | None:
    """Serialize a pydantic statistics section, or None when absent."""
    return model.model_dump(mode="json") if model is not None else None


def parse_iso_datetime(
    value: str | None, field_name: str | None = None, end_of_day: bool = False
) -> datetime | None:
    """Parse an ISO datetime string, or None when the value is empty.

    With ``end_of_day``, a date-only value becomes the last microsecond of that
    day so it works as an inclusive upper bound.

    Raises ValueError with a unified message on malformed input, including the
    field name and offending value when ``field_name`` is given.
    """
    if not value:
        return None
    try:
        return core_parse_iso_datetime(value, end_of_day=end_of_day)
    except ValueError as e:
        target = f" for '{field_name}'" if field_name else ""
        raise ValueError(
            f"Invalid datetime format{target}: {value!r}. "
            "Expected ISO format (e.g., '2025-12-11T09:00:00')"
        ) from e


def str_list(values: Any) -> list[Any]:
    """Coerce an optional iterable to a list (empty when falsy)."""
    return list(values) if values else []


def task_result(task: Any, message: str, **extra: Any) -> dict[str, Any]:
    """Standard mutation result: id, name, status, then extras and message."""
    return {
        "id": task.id,
        "name": task.name,
        "status": task.status.value,
        **extra,
        "message": message,
    }
