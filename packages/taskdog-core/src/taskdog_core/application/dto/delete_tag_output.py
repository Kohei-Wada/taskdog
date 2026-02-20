"""DTO for delete tag operation result."""

from dataclasses import dataclass


@dataclass
class DeleteTagOutput:
    """Result of deleting a tag.

    Attributes:
        tag_name: Name of the deleted tag
        affected_task_count: Number of tasks the tag was removed from
    """

    tag_name: str
    affected_task_count: int
