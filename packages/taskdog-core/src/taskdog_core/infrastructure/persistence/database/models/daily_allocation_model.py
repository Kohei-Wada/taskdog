"""SQLAlchemy ORM model for DailyAllocation entity.

This module defines the normalized daily allocation schema. Instead of storing
daily hour allocations as JSON in the tasks table, each (task_id, date, hours)
tuple is stored as a separate row, enabling:
- Efficient SQL aggregation (SUM, GROUP BY for workload calculations)
- Date range queries (tasks in a specific period)
- Atomic updates per date (no need to rewrite entire JSON)
- Database-level constraints (CHECK hours > 0)
"""

from datetime import date, datetime

from sqlalchemy import Date, Float, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .task_model import Base


class DailyAllocationModel(Base):
    """SQLAlchemy ORM model for normalized daily allocations.

    Maps to the 'daily_allocations' table in the database. Each row represents
    the hours allocated to a specific task on a specific date.

    Attributes:
        id: Primary key (auto-increment)
        task_id: Foreign key to tasks.id (CASCADE delete)
        date: The date of the allocation
        hours: Hours allocated on this date (must be > 0)
        created_at: Timestamp when the allocation was created
    """

    __tablename__ = "daily_allocations"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to task
    task_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )

    # Date of allocation
    date: Mapped[date] = mapped_column(Date, nullable=False)

    # Hours allocated (CHECK constraint added via migration)
    hours: Mapped[float] = mapped_column(Float, nullable=False)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    # Database constraints and indexes
    __table_args__ = (
        # Ensure unique (task_id, date) pairs
        UniqueConstraint("task_id", "date", name="uq_daily_allocations_task_date"),
        # Index for efficient task lookup
        Index("idx_daily_allocations_task_id", "task_id"),
        # Index for efficient date range queries
        Index("idx_daily_allocations_date", "date"),
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<DailyAllocationModel(id={self.id}, task_id={self.task_id}, "
            f"date={self.date}, hours={self.hours})>"
        )
