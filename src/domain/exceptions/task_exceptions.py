"""Custom exceptions for task operations."""


class TaskError(Exception):
    """Base exception for all task-related errors."""

    pass


class TaskNotFoundException(TaskError):
    """Raised when a task with given ID is not found."""

    def __init__(self, task_id: int) -> None:
        self.task_id = task_id
        super().__init__(f"Task with ID {task_id} not found")


class TaskValidationError(TaskError):
    """Raised when task validation fails."""

    pass


class TaskAlreadyFinishedError(TaskValidationError):
    """Raised when trying to start a task that is already finished."""

    def __init__(self, task_id: int, status: str) -> None:
        self.task_id = task_id
        self.status = status
        super().__init__(f"Cannot start task {task_id}: task is already {status}")


class TaskNotStartedError(TaskValidationError):
    """Raised when trying to complete a task that hasn't been started yet."""

    def __init__(self, task_id: int) -> None:
        self.task_id = task_id
        super().__init__(
            f"Cannot complete task {task_id}: task is PENDING. Start the task first with 'taskdog start {task_id}'"
        )
