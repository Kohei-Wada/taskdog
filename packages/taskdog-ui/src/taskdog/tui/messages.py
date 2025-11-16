"""Unified message formatting for TUI notifications.

This module provides a centralized message builder to ensure consistent
notification messages across TUI commands and WebSocket event handlers.
"""


class TUIMessageBuilder:
    """Centralized message formatting for TUI notifications."""

    @staticmethod
    def task_action(
        action: str, task_name: str, task_id: int, source_client_id: str | None = None
    ) -> str:
        """Standard format for task actions.

        Args:
            action: The action performed (e.g., "Started", "Completed", "Added task")
            task_name: Name of the task
            task_id: Task ID
            source_client_id: Optional client ID that performed the action (for remote operations)

        Returns:
            Formatted message string

        Examples:
            - Local: "Started: Task name (ID: 123)"
            - Remote: "Task started: Task name by client_abc"
        """
        base_msg = f"{action}: {task_name} (ID: {task_id})"
        if source_client_id:
            base_msg += f" by {source_client_id}"
        return base_msg

    @staticmethod
    def task_updated(
        task_id: int, fields: list[str], source_client_id: str | None = None
    ) -> str:
        """Standard format for task update operations.

        Args:
            task_id: Task ID
            fields: List of updated field names
            source_client_id: Optional client ID that performed the update

        Returns:
            Formatted message string

        Examples:
            - Local: "Updated task 123: priority, deadline"
            - Remote: "Updated task 123: priority, deadline by client_abc"
        """
        fields_str = ", ".join(fields)
        base_msg = f"Updated task {task_id}: {fields_str}"
        if source_client_id:
            base_msg += f" by {source_client_id}"
        return base_msg

    @staticmethod
    def batch_success(action: str, count: int) -> str:
        """Standard format for batch operation success messages.

        Args:
            action: The action performed (e.g., "Canceled", "Archived")
            count: Number of tasks affected

        Returns:
            Formatted message string

        Examples:
            - "Canceled 1 task"
            - "Archived 5 tasks"
        """
        singular = "task" if count == 1 else "tasks"
        return f"{action} {count} {singular}"

    @staticmethod
    def websocket_event(
        event_type: str,
        task_name: str,
        task_id: int | None = None,
        details: str = "",
        source_client_id: str | None = None,
    ) -> str:
        """Standard format for WebSocket event notifications.

        Args:
            event_type: The event type (e.g., "created", "deleted", "status changed")
            task_name: Name of the task
            task_id: Optional task ID
            details: Optional additional details (e.g., field changes, status transition)
            source_client_id: Optional client ID that triggered the event

        Returns:
            Formatted message string

        Examples:
            - "Task created: Task name (ID: 123) by client_abc"
            - "Task status changed: Task name (ID: 123) (PENDING → IN_PROGRESS) by client_abc"
        """
        base_msg = f"Task {event_type}: {task_name}"
        if task_id is not None:
            base_msg += f" (ID: {task_id})"
        if details:
            base_msg += f" ({details})"
        if source_client_id:
            base_msg += f" by {source_client_id}"
        return base_msg

    @staticmethod
    def note_saved(task_name: str, task_id: int) -> str:
        """Standard format for note save confirmation.

        Args:
            task_name: Name of the task
            task_id: Task ID

        Returns:
            Formatted message string

        Example:
            "Note saved for task: Task name (ID: 123)"
        """
        return f"Note saved for task: {task_name} (ID: {task_id})"

    @staticmethod
    def schedule_optimized(
        algorithm: str, scheduled_count: int, failed_count: int
    ) -> str:
        """Standard format for schedule optimization results.

        Args:
            algorithm: Optimization algorithm name
            scheduled_count: Number of successfully scheduled tasks
            failed_count: Number of tasks that failed to schedule

        Returns:
            Formatted message string

        Example:
            "Schedule optimized (greedy): 10 tasks scheduled, 2 failed"
        """
        return f"Schedule optimized ({algorithm}): {scheduled_count} tasks scheduled, {failed_count} failed"
