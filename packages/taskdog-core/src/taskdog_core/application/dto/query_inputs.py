"""Input DTOs for query use cases.

These DTOs encapsulate query parameters for task listing and filtering,
providing a presentation-agnostic interface for the Application layer.
"""

from dataclasses import dataclass, field
from datetime import date


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
        sort_by: Field to sort by (default: "id")
        reverse: Reverse sort order (default: False)
        include_gantt: If True, also build the Gantt overlay from the same fetch
        chart_start_date: Start date for the Gantt chart display range
        chart_end_date: End date for the Gantt chart display range
    """

    include_archived: bool = False
    status: str | None = None
    tags: list[str] = field(default_factory=list)
    match_all_tags: bool = False
    start_date: date | None = None
    end_date: date | None = None
    sort_by: str = "id"
    reverse: bool = False
    include_gantt: bool = False
    chart_start_date: date | None = None
    chart_end_date: date | None = None
