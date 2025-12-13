"""Unit tests for TaskUpdateBuilder."""

from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.infrastructure.persistence.database.models import TaskModel
from taskdog_core.infrastructure.persistence.database.models.task_model import Base
from taskdog_core.infrastructure.persistence.database.mutation_builders import (
    TaskUpdateBuilder,
)
from taskdog_core.infrastructure.persistence.mappers.task_db_mapper import TaskDbMapper


class TestTaskUpdateBuilder:
    """Test cases for TaskUpdateBuilder."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test database and builder."""
        # Create in-memory SQLite database
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.mapper = TaskDbMapper()
        yield
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_update_task_applies_changes(self):
        """Test that update_task applies changes to existing model."""
        # Create initial model
        initial_model = TaskModel(
            id=1,
            name="Old Name",
            priority=5,
            status="PENDING",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Updated task
        updated_task = Task(
            id=1,
            name="New Name",
            priority=10,
            status=TaskStatus.IN_PROGRESS,
            tags=[],
        )

        with self.Session() as session:
            session.add(initial_model)
            session.flush()

            builder = TaskUpdateBuilder(session, self.mapper)
            builder.update_task(initial_model, updated_task)

            # Verify changes applied
            assert initial_model.name == "New Name"
            assert initial_model.priority == 10
            assert initial_model.status == "IN_PROGRESS"

    def test_update_task_updates_timestamp(self):
        """Test that update_task automatically sets updated_at timestamp."""
        initial_model = TaskModel(
            id=1,
            name="Task",
            priority=5,
            status="PENDING",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        initial_model.updated_at = datetime(2020, 1, 1)

        updated_task = Task(
            id=1, name="Task Updated", priority=5, status=TaskStatus.PENDING, tags=[]
        )

        with self.Session() as session:
            session.add(initial_model)
            session.flush()

            before_update = initial_model.updated_at

            builder = TaskUpdateBuilder(session, self.mapper)
            builder.update_task(initial_model, updated_task)

            # Timestamp should be updated
            assert initial_model.updated_at != before_update
            assert initial_model.updated_at > before_update

    def test_update_task_does_not_commit(self):
        """Test that update_task does not commit the transaction."""
        initial_model = TaskModel(
            id=1,
            name="Old Name",
            priority=5,
            status="PENDING",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        updated_task = Task(
            id=1, name="New Name", priority=10, status=TaskStatus.PENDING, tags=[]
        )

        with self.Session() as session:
            session.add(initial_model)
            session.commit()

        with self.Session() as session:
            model = session.get(TaskModel, 1)
            builder = TaskUpdateBuilder(session, self.mapper)
            builder.update_task(model, updated_task)
            # Don't commit

        # Changes should not be persisted without commit
        with self.Session() as session:
            model = session.get(TaskModel, 1)
            assert model.name == "Old Name"  # Still old value

    def test_update_task_preserves_all_fields(self):
        """Test that update_task correctly updates all task fields."""
        now = datetime.now()
        initial_model = TaskModel(
            id=1,
            name="Old Task",
            priority=5,
            status="PENDING",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        updated_task = Task(
            id=1,
            name="Complete Task",
            priority=10,
            status=TaskStatus.IN_PROGRESS,
            planned_start=now,
            planned_end=now,
            deadline=now,
            estimated_duration=15.0,
            is_fixed=True,
            depends_on=[2, 3],
            tags=["urgent"],
        )

        with self.Session() as session:
            session.add(initial_model)
            session.flush()

            builder = TaskUpdateBuilder(session, self.mapper)
            builder.update_task(initial_model, updated_task)

            # Verify all fields updated
            assert initial_model.name == "Complete Task"
            assert initial_model.priority == 10
            assert initial_model.status == "IN_PROGRESS"
            assert initial_model.estimated_duration == 15.0
            assert initial_model.is_fixed is True
