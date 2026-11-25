"""Custom exceptions for notes operations."""

from taskdog_core.domain.exceptions.task_exceptions import TaskValidationError


class NotesTooLargeError(TaskValidationError):
    """Raised when appending would make a task's notes exceed the size limit."""

    def __init__(self, task_id: int, max_length: int) -> None:
        """Initialize with task ID and the maximum allowed notes length.

        Args:
            task_id: ID of the task whose notes would grow too large
            max_length: Maximum allowed notes length in characters
        """
        self.task_id = task_id
        self.max_length = max_length
        super().__init__(
            f"Appending would make the notes of task {task_id} "
            f"exceed {max_length} characters"
        )
