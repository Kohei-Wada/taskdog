"""Input DTOs for query use cases.

These DTOs encapsulate query parameters for task listing and filtering,
providing a presentation-agnostic interface for the Application layer.
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class TimeRange(Enum):
    """Time range presets for task queries.

    Attributes:
        CUSTOM: Custom date range (uses start_date/end_date)
        TODAY: Tasks relevant to today
        THIS_WEEK: Tasks relevant to this week
    """

    CUSTOM = "custom"
    TODAY = "today"
    THIS_WEEK = "this_week"


@dataclass
class ListTasksInput:
    """Input DTO for ListTasksUseCase.

    Encapsulates all filtering and sorting parameters for task list queries.
    Used by API routes, CLI, and TUI to request filtered task lists.

    Attributes:
        include_archived: Whether to include archived tasks (default: False)
        status: Filter by task status (e.g., "PENDING", "IN_PROGRESS")
        tags: Filter by tags (empty list means no tag filter)
        match_all_tags: If True, task must have all tags; if False, any tag matches
        start_date: Filter tasks with planned_start/end >= this date
        end_date: Filter tasks with planned_start/end <= this date
        time_range: Preset time range (TODAY, THIS_WEEK, or CUSTOM)
        sort_by: Field to sort by (default: "id")
        reverse: Reverse sort order (default: False)
    """

    include_archived: bool = False
    status: str | None = None
    tags: list[str] = field(default_factory=list)
    match_all_tags: bool = False
    start_date: date | None = None
    end_date: date | None = None
    time_range: TimeRange = TimeRange.CUSTOM
    sort_by: str = "id"
    reverse: bool = False


@dataclass
class GetGanttDataInput(ListTasksInput):
    """Input DTO for GetGanttDataUseCase.

    Extends ListTasksInput with Gantt chart-specific parameters.

    Attributes:
        chart_start_date: Start date for Gantt chart display
        chart_end_date: End date for Gantt chart display
    """

    chart_start_date: date | None = None
    chart_end_date: date | None = None
