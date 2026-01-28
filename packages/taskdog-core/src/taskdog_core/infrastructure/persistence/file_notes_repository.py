"""File-based repository for managing task notes.

This repository implements notes persistence using the local file system,
providing file-specific operations like path retrieval alongside the
standard NotesRepository interface.
"""

from pathlib import Path

from taskdog_core.domain.constants import MIN_FILE_SIZE_FOR_CONTENT
from taskdog_core.domain.repositories.notes_repository import NotesRepository
from taskdog_core.shared.xdg_utils import XDGDirectories


class FileNotesRepository(NotesRepository):
    """File-based implementation of notes repository.

    Stores task notes as markdown files in the XDG data directory.
    Provides both standard interface methods and file-specific operations.
    """

    def get_notes_path(self, task_id: int) -> Path:
        """Get path to task's markdown notes file.

        This is a file-system-specific method not part of the abstract interface.
        Used by presentation layer for editor integration.

        Args:
            task_id: Task ID

        Returns:
            Path to notes file at $XDG_DATA_HOME/taskdog/notes/{id}.md
        """
        return XDGDirectories.get_note_file(task_id)

    def has_notes(self, task_id: int) -> bool:
        """Check if task has an associated note file.

        Args:
            task_id: Task ID

        Returns:
            True if notes file exists and has content
        """
        try:
            return (
                self.get_notes_path(task_id).stat().st_size > MIN_FILE_SIZE_FOR_CONTENT
            )
        except OSError:
            return False

    def read_notes(self, task_id: int) -> str | None:
        """Read notes content for a task.

        Args:
            task_id: Task ID

        Returns:
            Notes content as string, or None if file doesn't exist or reading fails
        """
        notes_path = self.get_notes_path(task_id)

        if not notes_path.exists():
            return None

        try:
            return notes_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            # If reading fails (file permissions, encoding issues, etc.),
            # return None to maintain user experience
            return None

    def write_notes(self, task_id: int, content: str) -> None:
        """Write notes content for a task.

        Args:
            task_id: Task ID
            content: Notes content to write

        Raises:
            OSError: If writing fails
        """
        notes_path = self.get_notes_path(task_id)
        notes_path.write_text(content, encoding="utf-8")

    def ensure_notes_dir(self) -> None:
        """Ensure notes directory exists.

        Creates the notes directory if it doesn't exist.
        """
        XDGDirectories.get_notes_dir()

    def delete_notes(self, task_id: int) -> None:
        """Delete notes file for a task.

        Args:
            task_id: Task ID

        Note:
            Does not raise error if notes don't exist (idempotent operation)
        """
        notes_path = self.get_notes_path(task_id)
        notes_path.unlink(missing_ok=True)

    def get_task_ids_with_notes(self, task_ids: list[int]) -> set[int]:
        """Get task IDs that have notes from a list of task IDs.

        This is a batch operation that checks note existence for multiple tasks.
        For file-based storage, this still requires N stat() calls but allows
        for consistent interface with database-based storage.

        Args:
            task_ids: List of task IDs to check

        Returns:
            Set of task IDs that have notes
        """
        return {task_id for task_id in task_ids if self.has_notes(task_id)}
