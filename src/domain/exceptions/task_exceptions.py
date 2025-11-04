"""Custom exceptions for task operations."""

from typing import Any


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


class DependencyNotMetError(TaskValidationError):
    """Raised when trying to start a task with unmet dependencies."""

    def __init__(self, task_id: int, unmet_dependencies: list[int]) -> None:
        self.task_id = task_id
        self.unmet_dependencies = unmet_dependencies
        dep_ids = ", ".join(str(dep_id) for dep_id in unmet_dependencies)
        super().__init__(
            f"Cannot start task {task_id}: dependencies not met. Complete task(s) {dep_ids} first."
        )


class CorruptedDataError(TaskError):
    """Raised when tasks.json contains invalid data that violates entity invariants."""

    def __init__(self, corrupted_tasks: list[dict[str, Any]]) -> None:
        """Initialize with list of corrupted task data.

        Args:
            corrupted_tasks: List of dicts with 'data' and 'error' keys
        """
        self.corrupted_tasks = corrupted_tasks
        task_count = len(corrupted_tasks)

        # Build detailed error message
        error_lines = [
            f"Found {task_count} corrupted task(s) in tasks.json:",
            "",
        ]

        for item in corrupted_tasks:
            task_data = item["data"]
            error_msg = item["error"]
            task_id = task_data.get("id", "unknown")
            task_name = task_data.get("name", "")
            error_lines.append(f"  - Task ID {task_id} ('{task_name}'): {error_msg}")

        error_lines.extend(
            [
                "",
                "To fix this issue:",
                "  1. Manually edit tasks.json to fix the invalid data",
                "     - Empty names: Set to a non-empty string",
                "     - Invalid priority (≤0): Set to a positive integer (e.g., 5)",
                "     - Invalid duration (≤0): Set to null or a positive number",
                "  2. Delete tasks.json to start fresh (WARNING: this will lose all tasks)",
            ]
        )

        super().__init__("\n".join(error_lines))
