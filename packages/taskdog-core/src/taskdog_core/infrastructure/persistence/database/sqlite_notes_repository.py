"""SQLite-based repository for task notes using SQLAlchemy.

This repository provides database persistence for task notes using SQLite and
SQLAlchemy 2.0 ORM. It replaces file-based storage to eliminate N filesystem
stat() calls per task list request.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import delete, select

from taskdog_core.domain.repositories.notes_repository import NotesRepository
from taskdog_core.infrastructure.persistence.database.base_repository import (
    SqliteBaseRepository,
)
from taskdog_core.infrastructure.persistence.database.models.note_model import (
    NoteModel,
)

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

    from taskdog_core.domain.services.time_provider import ITimeProvider


class SqliteNotesRepository(SqliteBaseRepository, NotesRepository):
    """SQLite implementation of notes repository using SQLAlchemy ORM.

    This repository:
    - Uses SQLite database for persistence (same database as tasks)
    - Provides ACID transaction guarantees
    - Implements connection pooling via SQLAlchemy engine
    - Eliminates filesystem stat() calls for note existence checks
    """

    def __init__(
        self,
        database_url: str,
        time_provider: ITimeProvider,
        engine: Engine | None = None,
    ):
        """Initialize the repository with a SQLite database.

        Args:
            database_url: SQLAlchemy database URL (e.g., "sqlite:///path/to/db.sqlite")
            time_provider: Time provider for timestamps
            engine: SQLAlchemy Engine instance. If None, creates a new engine.
                   Pass a shared engine to avoid redundant connection pools.
        """
        super().__init__(database_url, engine)
        self.time_provider = time_provider

    def has_notes(self, task_id: int) -> bool:
        """Check if task has associated notes.

        Args:
            task_id: Task ID

        Returns:
            True if notes exist in database
        """
        with self.Session() as session:
            result = session.execute(
                select(NoteModel.task_id).where(NoteModel.task_id == task_id)
            ).scalar()
            return result is not None

    def read_notes(self, task_id: int) -> str | None:
        """Read notes content for a task.

        Args:
            task_id: Task ID

        Returns:
            Notes content as string, or None if not found
        """
        with self.Session() as session:
            note = session.get(NoteModel, task_id)
            if note is None:
                return None
            return str(note.content)

    def write_notes(self, task_id: int, content: str) -> None:
        """Write notes content for a task.

        Creates new note if it doesn't exist, updates if it does.

        Args:
            task_id: Task ID
            content: Notes content to write
        """
        now = self.time_provider.now()
        with self.Session() as session:
            existing = session.get(NoteModel, task_id)
            if existing is not None:
                existing.content = content
                existing.updated_at = now
            else:
                note = NoteModel(
                    task_id=task_id,
                    content=content,
                    created_at=now,
                    updated_at=now,
                )
                session.add(note)
            session.commit()

    def ensure_notes_dir(self) -> None:
        """No-op for database-based storage.

        This method exists for interface compatibility with file-based storage.
        Database storage doesn't need directory initialization.
        """

    def delete_notes(self, task_id: int) -> None:
        """Delete notes for a task.

        Args:
            task_id: Task ID

        Note:
            Does not raise error if notes don't exist (idempotent operation)
        """
        with self.Session() as session:
            session.execute(delete(NoteModel).where(NoteModel.task_id == task_id))
            session.commit()

    def get_task_ids_with_notes(self, task_ids: list[int]) -> set[int]:
        """Get task IDs that have notes from a list of task IDs.

        This is a batch operation that efficiently checks note existence for
        multiple tasks with a single database query.

        Args:
            task_ids: List of task IDs to check

        Returns:
            Set of task IDs that have notes
        """
        if not task_ids:
            return set()

        with self.Session() as session:
            result = session.execute(
                select(NoteModel.task_id).where(NoteModel.task_id.in_(task_ids))  # type: ignore[attr-defined]
            ).scalars()
            return set(result)

    def clear(self) -> None:
        """Delete all notes from the database.

        This method is primarily intended for testing purposes.
        """
        with self.Session() as session:
            session.execute(delete(NoteModel))
            session.commit()
