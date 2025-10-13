"""Custom exceptions for task operations."""


class TaskError(Exception):
    """Base exception for all task-related errors."""

    pass


class TaskNotFoundException(TaskError):
    """Raised when a task with given ID is not found."""

    def __init__(self, task_id: int):
        self.task_id = task_id
        super().__init__(f"Task with ID {task_id} not found")


class TaskValidationError(TaskError):
    """Raised when task validation fails."""

    pass


class CircularReferenceError(TaskValidationError):
    """Raised when a circular parent reference is detected."""

    def __init__(self, message: str = "Circular parent reference detected"):
        super().__init__(message)


class IncompleteChildrenError(TaskValidationError):
    """Raised when trying to complete a task with incomplete children."""

    def __init__(self, task_id: int, incomplete_children: list):
        self.task_id = task_id
        self.incomplete_children = incomplete_children
        children_ids = ", ".join(str(child.id) for child in incomplete_children)
        super().__init__(
            f"Cannot complete task {task_id}: has incomplete child tasks [{children_ids}]"
        )


class TaskWithChildrenError(TaskValidationError):
    """Raised when trying to start a task that has children."""

    def __init__(self, task_id: int, children: list):
        self.task_id = task_id
        self.children = children
        children_ids = ", ".join(str(child.id) for child in children)
        super().__init__(
            f"Cannot start task {task_id}: has child tasks [{children_ids}]. Start child tasks instead."
        )


class TaskAlreadyFinishedError(TaskValidationError):
    """Raised when trying to start a task that is already finished."""

    def __init__(self, task_id: int, status: str):
        self.task_id = task_id
        self.status = status
        super().__init__(f"Cannot start task {task_id}: task is already {status}")


class TaskNotStartedError(TaskValidationError):
    """Raised when trying to complete a task that hasn't been started yet."""

    def __init__(self, task_id: int):
        self.task_id = task_id
        super().__init__(
            f"Cannot complete task {task_id}: task is PENDING. Start the task first with 'taskdog start {task_id}'"
        )


class ParentTaskNotFoundError(TaskValidationError):
    """Raised when specified parent task doesn't exist."""

    def __init__(self, parent_id: int):
        self.parent_id = parent_id
        super().__init__(f"Parent task with ID {parent_id} does not exist")


class CannotSetEstimateForParentTaskError(TaskValidationError):
    """Raised when trying to set estimated_duration for a parent task."""

    def __init__(self, task_id: int, child_count: int):
        self.task_id = task_id
        self.child_count = child_count
        super().__init__(
            f"Cannot set estimated duration for parent task {task_id} "
            f"(has {child_count} child tasks). "
            "Parent task's estimated duration is automatically calculated from children."
        )


class DeadlineAfterParentError(TaskValidationError):
    """Raised when child task deadline is after parent task deadline."""

    def __init__(self, task_id: int, parent_id: int, task_deadline: str, parent_deadline: str):
        self.task_id = task_id
        self.parent_id = parent_id
        self.task_deadline = task_deadline
        self.parent_deadline = parent_deadline
        super().__init__(
            f"Cannot set deadline for task {task_id} to {task_deadline}: "
            f"parent task {parent_id} has earlier deadline {parent_deadline}"
        )
