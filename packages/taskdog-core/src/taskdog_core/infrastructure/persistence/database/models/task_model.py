"""SQLAlchemy ORM model for Task entity.

This module defines the database schema for tasks using SQLAlchemy 2.0 ORM.
Complex fields (daily_allocations, tags, depends_on) are
stored as JSON TEXT columns for Phase 2 implementation.
"""

from datetime import datetime

from sqlalchemy import Boolean, Float, Index, Integer, String, Text
from sqlalchemy.orm import (  # type: ignore[attr-defined]
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class TaskModel(Base):
    """SQLAlchemy ORM model for Task entity.

    Maps to the 'tasks' table in the database. This model uses JSON TEXT columns
    for complex fields (daily_allocations, tags, etc.) to maintain compatibility
    with the existing JSON-based storage during the migration phase.

    Schema corresponds to Task entity fields with SQLAlchemy types.
    """

    __tablename__ = "tasks"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Core task fields
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)

    # Schedule fields (nullable)
    planned_start: Mapped[datetime | None] = mapped_column(nullable=True)
    planned_end: Mapped[datetime | None] = mapped_column(nullable=True)
    deadline: Mapped[datetime | None] = mapped_column(nullable=True)

    # Actual time tracking (nullable)
    actual_start: Mapped[datetime | None] = mapped_column(nullable=True)
    actual_end: Mapped[datetime | None] = mapped_column(nullable=True)

    # Duration and scheduling
    estimated_duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_fixed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Complex fields stored as JSON TEXT
    # Format: {"2025-01-15": 2.0, "2025-01-16": 3.0}
    daily_allocations: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    # DEPRECATED: Kept for database backwards compatibility only.
    # This field is no longer used by the application but the column must exist
    # in the database schema because it has NOT NULL constraint.
    actual_daily_hours: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    # Format: [2, 3, 5]
    depends_on: Mapped[str] = mapped_column(Text, nullable=False, default="[]")

    # Archive flag
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationship to tags (many-to-many through task_tags)
    # Phase 6: All tags are stored in normalized schema (tags/task_tags tables).
    tag_models: Mapped[list["TagModel"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "TagModel",
        secondary="task_tags",
        back_populates="tasks",
        lazy="selectin",
    )

    # Database indexes for frequently queried columns
    __table_args__ = (
        Index("idx_status", "status"),
        Index("idx_is_archived", "is_archived"),
        Index("idx_deadline", "deadline"),
        Index("idx_planned_start", "planned_start"),
        Index("idx_priority", "priority"),
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<TaskModel(id={self.id}, name='{self.name}', status='{self.status}')>"
