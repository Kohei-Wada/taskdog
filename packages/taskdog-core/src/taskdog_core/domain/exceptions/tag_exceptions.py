"""Custom exceptions for tag operations."""

from taskdog_core.domain.exceptions.task_exceptions import TaskError


class TagNotFoundException(TaskError):
    """Raised when a tag with given name is not found."""

    def __init__(self, tag_name: str) -> None:
        self.tag_name = tag_name
        super().__init__(f"Tag '{tag_name}' not found")
