"""SQLite-based repository for task notes using SQLAlchemy.

This repository provides database persistence for task notes using SQLite and
SQLAlchemy 2.0 ORM. It replaces file-based storage to eliminate N filesystem
stat() calls per task list request.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError

from taskdog_core.domain.exceptions.notes_exceptions import NotesTooLargeError
from taskdog_core.domain.repositories.notes_repository import NotesRepository
from taskdog_core.infrastructure.persistence.database.base_repository import (
    SqliteBaseRepository,
)
from taskdog_core.infrastructure.persistence.database.models.note_model import (
    NoteModel,
)

if TYPE_CHECKING:
    from sqlalchemy.engine import CursorResult, Engine

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

        Notes are content-based: an empty note row (left behind by
        ``delete_notes``) counts as no notes.

        Args:
            task_id: Task ID

        Returns:
            True if a note with non-empty content exists in database
        """
        with self.Session() as session:
            result = session.execute(
                select(NoteModel.task_id).where(
                    NoteModel.task_id == task_id,
                    NoteModel.content != "",
                )
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

    def append_notes(
        self, task_id: int, content: str, max_length: int | None = None
    ) -> str:
        """Atomically append content to the notes of a task.

        The concatenation happens inside the database (a single
        ``UPDATE ... SET content = content || :content`` statement), so
        concurrent appends cannot lose each other's data. If ``max_length`` is
        given, the size check is part of the same statement's ``WHERE``
        clause, so concurrent appends cannot jointly exceed it either. If the
        note does not exist yet it is created with ``content``.

        Args:
            task_id: Task ID
            content: Content to append, added verbatim
            max_length: Maximum allowed length of the full notes after the
                append, or None for no limit

        Returns:
            The full notes content after the append

        Raises:
            NotesTooLargeError: If the append would exceed ``max_length``
                (the notes are left unchanged)
        """
        now = self.time_provider.now()
        with self.Session() as session:
            statement = update(NoteModel).where(NoteModel.task_id == task_id)
            if max_length is not None:
                statement = statement.where(
                    func.length(NoteModel.content) + len(content) <= max_length
                )
            statement = statement.values(
                content=NoteModel.content + content, updated_at=now
            )
            updated = cast("CursorResult[Any]", session.execute(statement))
            if updated.rowcount == 0:
                exists = session.execute(
                    select(NoteModel.task_id).where(NoteModel.task_id == task_id)
                ).scalar()
                if exists is not None or (
                    max_length is not None and len(content) > max_length
                ):
                    raise NotesTooLargeError(task_id, cast("int", max_length))
                try:
                    session.add(
                        NoteModel(
                            task_id=task_id,
                            content=content,
                            created_at=now,
                            updated_at=now,
                        )
                    )
                    session.flush()
                except IntegrityError:
                    # A concurrent writer created the note first: append to it.
                    session.rollback()
                    updated = cast("CursorResult[Any]", session.execute(statement))
                    if updated.rowcount == 0:
                        raise NotesTooLargeError(
                            task_id, cast("int", max_length)
                        ) from None
            result = session.execute(
                select(NoteModel.content).where(NoteModel.task_id == task_id)
            ).scalar_one()
            session.commit()
            return str(result)

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
                select(NoteModel.task_id).where(
                    NoteModel.task_id.in_(task_ids),  # type: ignore[attr-defined]
                    NoteModel.content != "",
                )
            ).scalars()
            return set(result)

    def clear(self) -> None:
        """Delete all notes from the database.

        This method is primarily intended for testing purposes.
        """
        with self.Session() as session:
            session.execute(delete(NoteModel))
            session.commit()
