"""ViewModels for Task table/list presentation.

These ViewModels contain task data needed for table/list rendering,
without domain entity references.
"""

from dataclasses import dataclass
from datetime import datetime

from presentation.enums.task_status import TaskStatus
from presentation.view_models.base import BaseViewModel


@dataclass(frozen=True)
class TaskRowViewModel(BaseViewModel):
    """ViewModel for a task row in table/list display.

    This contains all data needed to render a task in a table or list view.
    Unlike the domain Task entity, this is specifically for presentation
    and contains only the fields necessary for display.

    Attributes:
        id: Task ID
        name: Task name
        status: Task status
        priority: Task priority
        is_fixed: Whether task schedule is fixed
        estimated_duration: Estimated duration in hours (None if not set)
        actual_duration_hours: Actual duration in hours (None if not set)
        deadline: Deadline datetime (None if not set)
        planned_start: Planned start datetime (None if not set)
        planned_end: Planned end datetime (None if not set)
        actual_start: Actual start datetime (None if not set)
        actual_end: Actual end datetime (None if not set)
        depends_on: List of dependency task IDs
        tags: List of tags
        is_finished: Whether task is in a finished state (COMPLETED/CANCELED)
        has_notes: Whether task has associated notes
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: int
    name: str
    status: TaskStatus
    priority: int
    is_fixed: bool
    estimated_duration: float | None
    actual_duration_hours: float | None
    deadline: datetime | None
    planned_start: datetime | None
    planned_end: datetime | None
    actual_start: datetime | None
    actual_end: datetime | None
    depends_on: list[int]
    tags: list[str]
    is_finished: bool
    has_notes: bool
    created_at: datetime
    updated_at: datetime
