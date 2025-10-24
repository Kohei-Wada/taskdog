"""Repository for managing task notes files.

This repository handles all file system operations related to task notes,
implementing the Infrastructure layer responsibility for file I/O.
"""

from pathlib import Path

from shared.constants.time import MIN_FILE_SIZE_FOR_CONTENT
from shared.xdg_utils import XDGDirectories


class NotesRepository:
    """Repository for task notes file operations.

    Encapsulates all file system operations for task notes, isolating
    these infrastructure concerns from the Domain layer.
    """

    def get_notes_path(self, task_id: int) -> Path:
        """Get path to task's markdown notes file.

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
        notes_path = self.get_notes_path(task_id)
        return notes_path.exists() and notes_path.stat().st_size > MIN_FILE_SIZE_FOR_CONTENT

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
