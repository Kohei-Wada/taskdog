"""Shared serialization helpers for MCP tool responses."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datetime import datetime


def iso(dt: datetime | None) -> str | None:
    """ISO-format a datetime, or None."""
    return dt.isoformat() if dt else None


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
