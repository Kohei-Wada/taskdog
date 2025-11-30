"""SQLAlchemy ORM models for Tag entity and Task-Tag relationships.

This module defines the normalized tag schema for many-to-many relationships
between tasks and tags. Tags are stored in a separate table with unique names,
and task-tag associations are stored in a junction table.

This is part of Phase 1 implementation for Issue 228 (tag entity separation).
"""

from datetime import datetime

from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import (  # type: ignore[attr-defined]
    Mapped,
    mapped_column,
    relationship,
)

from .task_model import Base


class TagModel(Base):
    """SQLAlchemy ORM model for Tag entity.

    Maps to the 'tags' table in the database. Each tag has a unique name
    and can be associated with multiple tasks through the task_tags junction table.

    Attributes:
        id: Primary key (auto-increment)
        name: Tag name (unique, indexed)
        created_at: Timestamp when the tag was first created
    """

    __tablename__ = "tags"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Tag name (unique constraint)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    # Relationship to tasks (many-to-many through task_tags)
    tasks: Mapped[list["TaskModel"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "TaskModel",
        secondary="task_tags",
        back_populates="tag_models",
        lazy="selectin",
    )

    # Database indexes
    __table_args__ = (Index("idx_tag_name", "name"),)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<TagModel(id={self.id}, name='{self.name}')>"


class TaskTagModel(Base):
    """SQLAlchemy ORM model for Task-Tag association (junction table).

    Maps to the 'task_tags' table in the database. This junction table implements
    the many-to-many relationship between tasks and tags.

    Attributes:
        task_id: Foreign key to tasks.id
        tag_id: Foreign key to tags.id

    Composite Primary Key: (task_id, tag_id)
    """

    __tablename__ = "task_tags"

    # Foreign keys (composite primary key)
    task_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )

    # Database indexes for efficient lookups
    __table_args__ = (
        Index("idx_task_tags_task_id", "task_id"),
        Index("idx_task_tags_tag_id", "tag_id"),
        # Note: Composite primary key (task_id, tag_id) already ensures uniqueness
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<TaskTagModel(task_id={self.task_id}, tag_id={self.tag_id})>"
