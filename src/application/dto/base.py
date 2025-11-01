"""Base DTO classes for task operations."""

from dataclasses import dataclass


@dataclass
class SingleTaskInput:
    """Request data for single-task operations.

    This base class is used for operations that only require a task ID,
    such as starting, completing, pausing, removing, or archiving a task.

    Attributes:
        task_id: ID of the task to operate on
    """

    task_id: int
