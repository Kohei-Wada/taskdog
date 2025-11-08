"""Batch notes checker service to avoid N+1 query problem.

This module provides a service that fetches notes status for multiple tasks
in a single API call, eliminating the N+1 query problem that occurred when
checking notes status for each task individually.
"""

from taskdog.infrastructure.api_client import TaskdogApiClient


class BatchNotesChecker:
    """Service for checking task notes status in batch.

    This service maintains a cache of notes status and provides a method
    to load notes status for multiple tasks in a single API call.

    Attributes:
        _api_client: API client for communicating with the server.
        _cache: Cache of task_id to has_notes status.
    """

    def __init__(self, api_client: TaskdogApiClient):
        """Initialize the batch notes checker.

        Args:
            api_client: API client instance.
        """
        self._api_client = api_client
        self._cache: dict[int, bool] = {}

    def load_bulk(self, task_ids: list[int]) -> dict[int, bool]:
        """Load notes status for multiple tasks in batch.

        This method calls the batch notes endpoint to fetch notes status
        for all provided task IDs in a single API call, then caches the results.

        Args:
            task_ids: List of task IDs to check.

        Returns:
            Dictionary mapping task_id to has_notes boolean.
        """
        if not task_ids:
            return {}

        # Call batch API endpoint
        notes_status = self._api_client.get_notes_bulk(task_ids)

        # Update cache
        self._cache.update(notes_status)

        return notes_status

    def has_notes(self, task_id: int) -> bool:
        """Check if a task has notes (from cache).

        This method retrieves the notes status from the cache.
        If the task is not in the cache, it returns False.

        Note: You should call load_bulk() first to populate the cache.

        Args:
            task_id: Task ID to check.

        Returns:
            True if the task has notes, False otherwise.
        """
        return self._cache.get(task_id, False)

    def has_task_notes(self, task_id: int) -> bool:
        """Check if a task has notes (alias for has_notes).

        This method is an alias for has_notes() to match the API client interface
        that TablePresenter expects.

        Args:
            task_id: Task ID to check.

        Returns:
            True if the task has notes, False otherwise.
        """
        return self.has_notes(task_id)

    def clear_cache(self) -> None:
        """Clear the notes status cache.

        This should be called when tasks are modified (created, updated, deleted)
        to ensure the cache doesn't contain stale data.
        """
        self._cache.clear()
