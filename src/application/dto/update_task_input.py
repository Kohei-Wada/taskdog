"""DTO for updating a task."""

from typing import Optional, Union
from dataclasses import dataclass, field


# Sentinel value to distinguish "not provided" from "explicitly set to None"
class _Unset:
    """Sentinel class to represent an unset field."""
    pass


UNSET = _Unset()


@dataclass
class UpdateTaskInput:
    """Input data for updating a task.

    Attributes:
        task_id: ID of the task to update
        name: New name (optional)
        priority: New priority (optional)
        status: New status (optional)
        parent_id: New parent task ID (UNSET=don't update, None=clear parent, int=set parent)
        planned_start: New planned start (optional)
        planned_end: New planned end (optional)
        deadline: New deadline (optional)
        estimated_duration: New estimated duration (optional)
    """

    task_id: int
    name: Optional[str] = None
    priority: Optional[int] = None
    status: Optional[str] = None
    parent_id: Union[int, None, _Unset] = field(default=UNSET)
    planned_start: Optional[str] = None
    planned_end: Optional[str] = None
    deadline: Optional[str] = None
    estimated_duration: Optional[float] = None
