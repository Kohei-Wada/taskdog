"""Shared serialization helpers for MCP tool responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any


def iso(dt: datetime | None) -> str | None:
    """ISO-format a datetime, or None."""
    return dt.isoformat() if dt else None


def parse_iso_datetime(
    value: str | None, field_name: str | None = None
) -> datetime | None:
    """Parse an ISO datetime string, or None when the value is empty.

    Raises ValueError with a unified message on malformed input, including the
    field name and offending value when ``field_name`` is given.
    """
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
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
