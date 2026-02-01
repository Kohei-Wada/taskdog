"""Unit tests for DailyAllocationBuilder."""

from datetime import date, datetime

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from taskdog_core.infrastructure.persistence.database.models import (
    DailyAllocationModel,
    TaskModel,
)
from taskdog_core.infrastructure.persistence.database.models.task_model import Base
from taskdog_core.infrastructure.persistence.database.mutation_builders import (
    DailyAllocationBuilder,
)


class TestDailyAllocationBuilder:
    """Test cases for DailyAllocationBuilder."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test database and builder."""
        # Create in-memory SQLite database
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        yield
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_sync_daily_allocations_adds_new_allocations(self):
        """Test that sync_daily_allocations adds new allocations to task."""
        with self.Session() as session:
            # Create initial task
            task_model = TaskModel(
                id=1,
                name="Task",
                priority=5,
                status="PENDING",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            session.add(task_model)
            session.flush()

            builder = DailyAllocationBuilder(session)
            allocations = {
                date(2025, 1, 15): 2.0,
                date(2025, 1, 16): 3.0,
            }
            builder.sync_daily_allocations(task_model, allocations)
            session.commit()

        # Verify allocations were added
        with self.Session() as session:
            stmt = select(DailyAllocationModel).where(DailyAllocationModel.task_id == 1)
            records = session.scalars(stmt).all()
            assert len(records) == 2

            records_by_date = {r.date: r.hours for r in records}
            assert records_by_date[date(2025, 1, 15)] == 2.0
            assert records_by_date[date(2025, 1, 16)] == 3.0

    def test_sync_daily_allocations_clears_existing_allocations(self):
        """Test that sync_daily_allocations clears existing allocations."""
        with self.Session() as session:
            # Create task with initial allocations
            task_model = TaskModel(
                id=1,
                name="Task",
                priority=5,
                status="PENDING",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            session.add(task_model)
            session.flush()

            # Add initial allocations
            session.add(
                DailyAllocationModel(
                    task_id=1,
                    date=date(2025, 1, 10),
                    hours=4.0,
                    created_at=datetime.now(),
                )
            )
            session.commit()

        with self.Session() as session:
            task_model = session.get(TaskModel, 1)
            builder = DailyAllocationBuilder(session)

            # Sync with different allocations
            allocations = {
                date(2025, 1, 15): 2.0,
            }
            builder.sync_daily_allocations(task_model, allocations)
            session.commit()

        # Verify old allocation is replaced
        with self.Session() as session:
            stmt = select(DailyAllocationModel).where(DailyAllocationModel.task_id == 1)
            records = session.scalars(stmt).all()
            assert len(records) == 1
            assert records[0].date == date(2025, 1, 15)
            assert records[0].hours == 2.0

    def test_sync_daily_allocations_with_empty_dict_clears_all(self):
        """Test that sync_daily_allocations with empty dict clears all allocations."""
        with self.Session() as session:
            # Create task with initial allocations
            task_model = TaskModel(
                id=1,
                name="Task",
                priority=5,
                status="PENDING",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            session.add(task_model)
            session.flush()

            # Add initial allocations
            session.add(
                DailyAllocationModel(
                    task_id=1,
                    date=date(2025, 1, 10),
                    hours=4.0,
                    created_at=datetime.now(),
                )
            )
            session.add(
                DailyAllocationModel(
                    task_id=1,
                    date=date(2025, 1, 11),
                    hours=3.0,
                    created_at=datetime.now(),
                )
            )
            session.commit()

        with self.Session() as session:
            task_model = session.get(TaskModel, 1)
            builder = DailyAllocationBuilder(session)

            # Sync with empty dict
            builder.sync_daily_allocations(task_model, {})
            session.commit()

        # Verify all allocations are cleared
        with self.Session() as session:
            stmt = select(DailyAllocationModel).where(DailyAllocationModel.task_id == 1)
            records = session.scalars(stmt).all()
            assert len(records) == 0

    def test_sync_daily_allocations_skips_zero_hours(self):
        """Test that sync_daily_allocations skips allocations with zero hours."""
        with self.Session() as session:
            task_model = TaskModel(
                id=1,
                name="Task",
                priority=5,
                status="PENDING",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            session.add(task_model)
            session.flush()

            builder = DailyAllocationBuilder(session)
            allocations = {
                date(2025, 1, 15): 2.0,
                date(2025, 1, 16): 0.0,  # Should be skipped
                date(2025, 1, 17): 3.0,
            }
            builder.sync_daily_allocations(task_model, allocations)
            session.commit()

        # Verify only non-zero allocations were added
        with self.Session() as session:
            stmt = select(DailyAllocationModel).where(DailyAllocationModel.task_id == 1)
            records = session.scalars(stmt).all()
            assert len(records) == 2

            dates = {r.date for r in records}
            assert date(2025, 1, 15) in dates
            assert date(2025, 1, 16) not in dates  # Zero hours skipped
            assert date(2025, 1, 17) in dates

    def test_sync_daily_allocations_skips_negative_hours(self):
        """Test that sync_daily_allocations skips allocations with negative hours."""
        with self.Session() as session:
            task_model = TaskModel(
                id=1,
                name="Task",
                priority=5,
                status="PENDING",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            session.add(task_model)
            session.flush()

            builder = DailyAllocationBuilder(session)
            allocations = {
                date(2025, 1, 15): 2.0,
                date(2025, 1, 16): -1.0,  # Should be skipped
            }
            builder.sync_daily_allocations(task_model, allocations)
            session.commit()

        # Verify only positive allocations were added
        with self.Session() as session:
            stmt = select(DailyAllocationModel).where(DailyAllocationModel.task_id == 1)
            records = session.scalars(stmt).all()
            assert len(records) == 1
            assert records[0].hours == 2.0

    def test_sync_daily_allocations_does_not_affect_other_tasks(self):
        """Test that sync_daily_allocations only affects the specified task."""
        with self.Session() as session:
            # Create two tasks with allocations
            task1 = TaskModel(
                id=1,
                name="Task 1",
                priority=5,
                status="PENDING",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            task2 = TaskModel(
                id=2,
                name="Task 2",
                priority=5,
                status="PENDING",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            session.add_all([task1, task2])
            session.flush()

            # Add allocations to both tasks
            session.add(
                DailyAllocationModel(
                    task_id=1,
                    date=date(2025, 1, 10),
                    hours=4.0,
                    created_at=datetime.now(),
                )
            )
            session.add(
                DailyAllocationModel(
                    task_id=2,
                    date=date(2025, 1, 11),
                    hours=5.0,
                    created_at=datetime.now(),
                )
            )
            session.commit()

        with self.Session() as session:
            task1 = session.get(TaskModel, 1)
            builder = DailyAllocationBuilder(session)

            # Sync task 1 only
            builder.sync_daily_allocations(task1, {date(2025, 1, 15): 2.0})
            session.commit()

        # Verify task 2's allocations are unchanged
        with self.Session() as session:
            stmt = select(DailyAllocationModel).where(DailyAllocationModel.task_id == 2)
            records = session.scalars(stmt).all()
            assert len(records) == 1
            assert records[0].date == date(2025, 1, 11)
            assert records[0].hours == 5.0

    def test_sync_daily_allocations_does_not_commit(self):
        """Test that sync_daily_allocations does not commit the transaction."""
        with self.Session() as session:
            task_model = TaskModel(
                id=1,
                name="Task",
                priority=5,
                status="PENDING",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            session.add(task_model)
            session.commit()

        with self.Session() as session:
            task_model = session.get(TaskModel, 1)
            builder = DailyAllocationBuilder(session)
            builder.sync_daily_allocations(task_model, {date(2025, 1, 15): 2.0})
            # Don't commit

        # Allocations should not be persisted without commit
        with self.Session() as session:
            stmt = select(DailyAllocationModel).where(DailyAllocationModel.task_id == 1)
            records = session.scalars(stmt).all()
            assert len(records) == 0

    def test_sync_daily_allocations_persists_on_commit(self):
        """Test that sync_daily_allocations persists when session commits."""
        with self.Session() as session:
            task_model = TaskModel(
                id=1,
                name="Task",
                priority=5,
                status="PENDING",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            session.add(task_model)
            session.flush()

            builder = DailyAllocationBuilder(session)
            builder.sync_daily_allocations(task_model, {date(2025, 1, 15): 2.0})
            session.commit()

        # Allocations should be persisted after commit
        with self.Session() as session:
            stmt = select(DailyAllocationModel).where(DailyAllocationModel.task_id == 1)
            records = session.scalars(stmt).all()
            assert len(records) == 1
            assert records[0].date == date(2025, 1, 15)
            assert records[0].hours == 2.0

    def test_sync_daily_allocations_skips_task_without_id(self):
        """Test that sync_daily_allocations does nothing for task without ID."""
        with self.Session() as session:
            # Create task model without adding to session (no ID yet)
            task_model = TaskModel(
                id=None,
                name="Task",
                priority=5,
                status="PENDING",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            builder = DailyAllocationBuilder(session)
            # Should not raise, just skip
            builder.sync_daily_allocations(task_model, {date(2025, 1, 15): 2.0})
            session.commit()

        # No allocations should be created
        with self.Session() as session:
            stmt = select(DailyAllocationModel)
            records = session.scalars(stmt).all()
            assert len(records) == 0

    def test_sync_daily_allocations_sets_created_at(self):
        """Test that sync_daily_allocations sets created_at timestamp."""
        before = datetime.now()

        with self.Session() as session:
            task_model = TaskModel(
                id=1,
                name="Task",
                priority=5,
                status="PENDING",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            session.add(task_model)
            session.flush()

            builder = DailyAllocationBuilder(session)
            builder.sync_daily_allocations(task_model, {date(2025, 1, 15): 2.0})
            session.commit()

        after = datetime.now()

        # Verify created_at is set correctly
        with self.Session() as session:
            stmt = select(DailyAllocationModel).where(DailyAllocationModel.task_id == 1)
            record = session.scalars(stmt).first()
            assert record is not None
            assert before <= record.created_at <= after
