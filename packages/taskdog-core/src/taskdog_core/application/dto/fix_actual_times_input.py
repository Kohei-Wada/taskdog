"""DTO for fixing actual start/end timestamps and duration."""

from dataclasses import dataclass
from datetime import datetime
from types import EllipsisType


@dataclass
class FixActualTimesInput:
    """Request data for fixing actual timestamps and duration.

    Used to correct actual_start, actual_end, and actual_duration
    after the fact, for historical accuracy. Uses Ellipsis (...) as
    sentinel to distinguish "not provided" from None (explicit clear).

    Attributes:
        task_id: ID of the task to fix
        actual_start: New actual start (None to clear, ... to keep current)
        actual_end: New actual end (None to clear, ... to keep current)
        actual_duration: Explicit duration in hours (None to clear, ... to keep current)
    """

    task_id: int
    actual_start: datetime | None | EllipsisType = ...
    actual_end: datetime | None | EllipsisType = ...
    actual_duration: float | None | EllipsisType = ...
