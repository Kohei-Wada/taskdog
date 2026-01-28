"""In-memory repository implementations for testing.

These implementations store data in memory and can be easily cleared between tests.
"""


class InMemoryNotesRepository:
    """In-memory notes repository for testing.

    Provides a simple dict-based storage for notes that can be cleared between tests.
    """

    def __init__(self):
        self._notes: dict[int, str] = {}

    def has_notes(self, task_id: int) -> bool:
        """Check if task has notes."""
        return task_id in self._notes and len(self._notes[task_id]) > 0

    def read_notes(self, task_id: int) -> str | None:
        """Read notes for task."""
        return self._notes.get(task_id)

    def write_notes(self, task_id: int, content: str) -> None:
        """Write notes for task."""
        self._notes[task_id] = content

    def delete_notes(self, task_id: int) -> None:
        """Delete notes for task."""
        if task_id in self._notes:
            del self._notes[task_id]

    def ensure_notes_dir(self) -> None:
        """No-op for in-memory implementation."""
        pass

    def get_task_ids_with_notes(self, task_ids: list[int]) -> set[int]:
        """Get task IDs that have notes from a list of task IDs."""
        return {task_id for task_id in task_ids if self.has_notes(task_id)}

    def clear(self) -> None:
        """Clear all notes. Used between tests for isolation."""
        self._notes.clear()
