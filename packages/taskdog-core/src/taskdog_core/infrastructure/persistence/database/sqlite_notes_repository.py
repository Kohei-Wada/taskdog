"""SQLite-based repository for task notes using SQLAlchemy.

This repository provides database persistence for task notes using SQLite and
SQLAlchemy 2.0 ORM. It replaces file-based storage to eliminate N filesystem
stat() calls per task list request.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from taskdog_core.domain.repositories.notes_repository import NotesRepository
from taskdog_core.domain.services.time_provider import ITimeProvider
from taskdog_core.infrastructure.persistence.database.base_repository import (
    SqliteBaseRepository,
)
from taskdog_core.infrastructure.persistence.database.models.note_model import (
    NoteModel,
)


@dataclass
class MigrationResult:
    """Result of migrating notes from files to database."""

    migrated: int
    skipped: int
    errors: int
    error_messages: list[str]


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
        pass

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

    def migrate_from_files(self, notes_dir: Path) -> MigrationResult:
        """Migrate notes from filesystem to database.

        This is an idempotent operation that reads all {task_id}.md files
        from the notes directory and inserts them into the database. Notes
        that already exist in the database are skipped.

        Args:
            notes_dir: Path to the notes directory containing .md files

        Returns:
            MigrationResult with counts of migrated/skipped/errors
        """
        migrated = 0
        skipped = 0
        errors = 0
        error_messages: list[str] = []

        if not notes_dir.exists():
            return MigrationResult(migrated, skipped, errors, error_messages)

        # First pass: collect all valid task IDs and their files
        file_task_mapping: dict[int, Path] = {}
        for note_file in notes_dir.glob("*.md"):
            try:
                task_id = int(note_file.stem)
                file_task_mapping[task_id] = note_file
            except ValueError:
                errors += 1
                error_messages.append(f"Invalid filename: {note_file.name}")

        if not file_task_mapping:
            return MigrationResult(migrated, skipped, errors, error_messages)

        # Batch check for existing notes to avoid N+1 queries
        existing_task_ids = self.get_task_ids_with_notes(list(file_task_mapping.keys()))

        # Second pass: migrate notes that don't exist in database
        for task_id, note_file in file_task_mapping.items():
            # Check if note already exists in database
            if task_id in existing_task_ids:
                skipped += 1
                continue

            # Read file content
            try:
                content = note_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as e:
                errors += 1
                error_messages.append(f"Failed to read {note_file.name}: {e}")
                continue

            # Skip empty files
            if not content.strip():
                skipped += 1
                continue

            # Get file timestamps for created_at and updated_at
            stat = note_file.stat()
            created_at = datetime.fromtimestamp(stat.st_ctime)
            updated_at = datetime.fromtimestamp(stat.st_mtime)

            # Insert into database
            try:
                with self.Session() as session:
                    note = NoteModel(
                        task_id=task_id,
                        content=content,
                        created_at=created_at,
                        updated_at=updated_at,
                    )
                    session.add(note)
                    session.commit()
                migrated += 1
            except SQLAlchemyError as e:
                errors += 1
                error_messages.append(f"Failed to insert note for task {task_id}: {e}")

        return MigrationResult(migrated, skipped, errors, error_messages)

    def clear(self) -> None:
        """Delete all notes from the database.

        This method is primarily intended for testing purposes.
        """
        with self.Session() as session:
            session.execute(delete(NoteModel))
            session.commit()
