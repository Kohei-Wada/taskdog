"""DTO for setting task tags."""

from dataclasses import dataclass


@dataclass
class SetTaskTagsInput:
    """Request data for setting task tags.

    Attributes:
        task_id: ID of the task to update
        tags: List of tags to set (completely replaces existing tags)
    """

    task_id: int
    tags: list[str]
