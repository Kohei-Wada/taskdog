"""Custom exceptions for task operations."""

from typing import Any


class TaskError(Exception):
    """Base exception for all task-related errors."""

    pass


class TaskNotFoundException(TaskError):
    """Raised when a task with given ID is not found."""

    def __init__(self, task_id: int | str) -> None:
        if isinstance(task_id, str):
            # Already formatted message from API (avoids double formatting)
            super().__init__(task_id)
            self.task_id = None  # Can't extract ID from message
        else:
            # Traditional usage with task ID
            self.task_id = task_id
            super().__init__(f"Task with ID {task_id} not found")


class TaskValidationError(TaskError):
    """Raised when task validation fails."""

    pass


class TaskAlreadyFinishedError(TaskValidationError):
    """Raised when trying to modify a task that is already finished.

    This error is used for multiple operations: start, complete, cancel, and pause.
    """

    def __init__(self, task_id: int, status: str, operation: str = "start") -> None:
        self.task_id = task_id
        self.status = status
        self.operation = operation
        super().__init__(f"Cannot {operation} task {task_id}: task is already {status}")


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


class ServerConnectionError(TaskError):
    """Raised when connection to the API server fails."""

    def __init__(self, base_url: str, original_error: Exception) -> None:
        """Initialize with server URL and original error.

        Args:
            base_url: Base URL of the API server
            original_error: Original exception from httpx
        """
        self.base_url = base_url
        self.original_error = original_error
        super().__init__(
            f"Cannot connect to server at {base_url}: {type(original_error).__name__}: {original_error}"
        )


class TaskNotSchedulableError(TaskValidationError):
    """Raised when a single task cannot be scheduled."""

    def __init__(self, task_id: int, reason: str) -> None:
        """Initialize with task ID and reason.

        Args:
            task_id: ID of the task that cannot be scheduled
            reason: Human-readable reason why the task is not schedulable
        """
        self.task_id = task_id
        self.reason = reason
        super().__init__(f"Cannot schedule task {task_id}: {reason}")


class NoSchedulableTasksError(TaskValidationError):
    """Raised when no tasks can be scheduled during optimization."""

    def __init__(
        self, task_ids: list[int] | None = None, reasons: dict[int, str] | None = None
    ) -> None:
        """Initialize with optional task IDs and reasons.

        Args:
            task_ids: Specific task IDs that were requested (None if all tasks)
            reasons: Dict mapping task ID to reason why it's not schedulable
        """
        self.task_ids = task_ids
        self.reasons = reasons or {}

        if task_ids:
            # Specific tasks were requested
            if len(task_ids) == 1:
                task_id = task_ids[0]
                reason = self.reasons.get(task_id, "Task is not schedulable")
                super().__init__(f"Cannot optimize task {task_id}: {reason}")
            else:
                # Build detailed message for multiple tasks
                lines = ["Cannot optimize the specified tasks:"]
                for task_id in task_ids:
                    reason = self.reasons.get(task_id, "Task is not schedulable")
                    lines.append(f"  - Task {task_id}: {reason}")
                super().__init__("\n".join(lines))
        else:
            # No specific tasks requested (all tasks)
            super().__init__(
                "No schedulable tasks found. All tasks are either completed, in progress, fixed, or already scheduled."
            )
