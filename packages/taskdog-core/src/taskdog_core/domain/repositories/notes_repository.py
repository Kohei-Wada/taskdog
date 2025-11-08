"""Abstract interface for notes repository.

This interface defines the contract for managing task notes,
abstracting away implementation details like file system operations.
"""

from abc import ABC, abstractmethod


class NotesRepository(ABC):
    """Abstract interface for task notes persistence.

    This interface provides implementation-agnostic methods for notes management.
    Implementation-specific methods (like get_notes_path for file-based storage)
    should be defined in concrete implementations.
    """

    @abstractmethod
    def has_notes(self, task_id: int) -> bool:
        """Check if task has associated notes.

        Args:
            task_id: Task ID

        Returns:
            True if notes exist and have content
        """
        pass

    @abstractmethod
    def read_notes(self, task_id: int) -> str | None:
        """Read notes content for a task.

        Args:
            task_id: Task ID

        Returns:
            Notes content as string, or None if not found or reading fails
        """
        pass

    @abstractmethod
    def write_notes(self, task_id: int, content: str) -> None:
        """Write notes content for a task.

        Args:
            task_id: Task ID
            content: Notes content to write

        Raises:
            OSError: If writing fails
        """
        pass

    @abstractmethod
    def ensure_notes_dir(self) -> None:
        """Ensure notes storage is initialized.

        Creates necessary storage structure if it doesn't exist.
        """
        pass
