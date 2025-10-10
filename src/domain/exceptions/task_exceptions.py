"""Custom exceptions for task operations."""


class TaskException(Exception):
    """Base exception for all task-related errors."""

    pass


class TaskNotFoundException(TaskException):
    """Raised when a task with given ID is not found."""

    def __init__(self, task_id: int):
        self.task_id = task_id
        super().__init__(f"Task with ID {task_id} not found")


class TaskValidationError(TaskException):
    """Raised when task validation fails."""

    pass


class CircularReferenceError(TaskValidationError):
    """Raised when a circular parent reference is detected."""

    def __init__(self, message: str = "Circular parent reference detected"):
        super().__init__(message)
