"""Builder for managing daily allocation records.

This builder handles the synchronization of daily allocations in the
normalized database schema (daily_allocations table).
"""

from datetime import date, datetime

from sqlalchemy import delete
from sqlalchemy.orm import Session

from taskdog_core.infrastructure.persistence.database.models import (
    DailyAllocationModel,
    TaskModel,
)


class DailyAllocationBuilder:
    """Builder for managing daily allocation records.

    This builder provides methods to synchronize daily allocations,
    handling the daily_allocations table operations. It performs a
    complete replacement strategy (delete all, then insert new).

    Example:
        >>> builder = DailyAllocationBuilder(session)
        >>> builder.sync_daily_allocations(task_model, {date(2025, 1, 15): 2.0})
    """

    def __init__(self, session: Session):
        """Initialize the builder.

        Args:
            session: SQLAlchemy session for database operations
        """
        self._session = session

    def sync_daily_allocations(
        self, task_model: TaskModel, allocations: dict[date, float]
    ) -> None:
        """Synchronize task's daily allocations (replaces existing allocations).

        This method performs a complete replacement of daily allocations:
        1. Deletes all existing allocations for this task
        2. If allocations is empty, stops here
        3. Inserts new allocation records

        Args:
            task_model: The TaskModel instance to update
            allocations: Dictionary mapping dates to hours (replaces all existing)

        Note:
            - This is a full replacement, not an append operation
            - Zero or negative hours should be filtered out before calling
            - The task must be flushed (have an ID) before calling this method
        """
        if task_model.id is None:
            # Task hasn't been persisted yet
            return

        # Delete existing allocations for this task
        self._session.execute(
            delete(DailyAllocationModel).where(
                DailyAllocationModel.task_id == task_model.id
            )
        )

        if not allocations:
            # No allocations to insert
            return

        # Insert new allocations
        now = datetime.now()
        for allocation_date, hours in allocations.items():
            if hours <= 0:
                # Skip zero or negative allocations
                continue

            self._session.add(
                DailyAllocationModel(
                    task_id=task_model.id,
                    date=allocation_date,
                    hours=hours,
                    created_at=now,
                )
            )
