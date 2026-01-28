"""SQLAlchemy ORM model for Note entity.

This module defines the database schema for task notes using SQLAlchemy 2.0 ORM.
Notes are stored in the database to eliminate N filesystem stat() calls per
task list request.
"""

from datetime import datetime

from sqlalchemy import ForeignKey, Index, Integer, Text
from sqlalchemy.orm import (  # type: ignore[attr-defined]
    Mapped,
    mapped_column,
)

from .task_model import Base


class NoteModel(Base):
    """SQLAlchemy ORM model for Note entity.

    Maps to the 'notes' table in the database. Each note is associated with
    exactly one task via foreign key. Notes are automatically deleted when
    their parent task is deleted (CASCADE).

    This model replaces the file-based storage in ~/.local/share/taskdog/notes/
    to improve performance by eliminating filesystem stat() calls.
    """

    __tablename__ = "notes"

    # Primary key is task_id (one note per task)
    task_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Note content (markdown)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)

    # Index on task_id for efficient lookups
    # (Primary key automatically creates an index, but being explicit)
    __table_args__ = (Index("idx_notes_task_id", "task_id"),)

    def __repr__(self) -> str:
        """String representation for debugging."""
        content_preview = (
            self.content[:50] + "..." if len(self.content) > 50 else self.content
        )
        return f"<NoteModel(task_id={self.task_id}, content='{content_preview}')>"
