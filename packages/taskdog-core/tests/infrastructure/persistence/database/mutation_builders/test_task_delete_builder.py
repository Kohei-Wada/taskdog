"""Unit tests for TaskDeleteBuilder."""

from datetime import datetime

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from taskdog_core.infrastructure.persistence.database.models import TaskModel
from taskdog_core.infrastructure.persistence.database.models.task_model import Base
from taskdog_core.infrastructure.persistence.database.mutation_builders import (
    TaskDeleteBuilder,
)


class TestTaskDeleteBuilder:
    """Test cases for TaskDeleteBuilder."""

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

    def test_delete_task_removes_model(self):
        """Test that delete_task removes the model from session."""
        # Create initial model
        initial_model = TaskModel(
            id=1,
            name="Task to Delete",
            priority=5,
            status="PENDING",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        with self.Session() as session:
            session.add(initial_model)
            session.commit()

        with self.Session() as session:
            builder = TaskDeleteBuilder(session)
            result = builder.delete_task(1)
            session.commit()

            # Should return True
            assert result is True

        # Task should be deleted
        with self.Session() as session:
            stmt = select(TaskModel)
            models = session.scalars(stmt).all()
            assert len(models) == 0

    def test_delete_task_returns_true_when_found(self):
        """Test that delete_task returns True when task exists."""
        initial_model = TaskModel(
            id=1,
            name="Task",
            priority=5,
            status="PENDING",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        with self.Session() as session:
            session.add(initial_model)
            session.commit()

        with self.Session() as session:
            builder = TaskDeleteBuilder(session)
            result = builder.delete_task(1)

            assert result is True

    def test_delete_task_returns_false_when_not_found(self):
        """Test that delete_task returns False when task doesn't exist."""
        with self.Session() as session:
            builder = TaskDeleteBuilder(session)
            result = builder.delete_task(999)

            # Should return False for nonexistent task
            assert result is False

    def test_delete_task_does_not_commit(self):
        """Test that delete_task does not commit the transaction."""
        initial_model = TaskModel(
            id=1,
            name="Task",
            priority=5,
            status="PENDING",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        with self.Session() as session:
            session.add(initial_model)
            session.commit()

        with self.Session() as session:
            builder = TaskDeleteBuilder(session)
            builder.delete_task(1)
            # Don't commit

        # Task should still exist without commit
        with self.Session() as session:
            stmt = select(TaskModel)
            models = session.scalars(stmt).all()
            assert len(models) == 1
