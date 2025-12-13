"""Unit tests for TaskInsertBuilder."""

from datetime import datetime

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.infrastructure.persistence.database.models import TaskModel
from taskdog_core.infrastructure.persistence.database.models.task_model import Base
from taskdog_core.infrastructure.persistence.database.mutation_builders import (
    TaskInsertBuilder,
)
from taskdog_core.infrastructure.persistence.mappers.task_db_mapper import TaskDbMapper


class TestTaskInsertBuilder:
    """Test cases for TaskInsertBuilder."""

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

    def test_insert_task_creates_model(self):
        """Test that insert_task creates a TaskModel in the session."""
        task = Task(
            id=1,
            name="Test Task",
            priority=5,
            status=TaskStatus.PENDING,
            tags=[],
        )

        with self.Session() as session:
            builder = TaskInsertBuilder(session, self.mapper)
            model = builder.insert_task(task)

            # Model should be created and flushed
            assert isinstance(model, TaskModel)
            assert model.name == "Test Task"
            assert model.priority == 5
            assert model.status == "PENDING"

            # Model should be in session
            assert model in session

    def test_insert_task_flushes_for_id(self):
        """Test that insert_task flushes to get ID immediately."""
        task = Task(
            id=1,
            name="Test Task",
            priority=5,
            status=TaskStatus.PENDING,
            tags=[],
        )

        with self.Session() as session:
            builder = TaskInsertBuilder(session, self.mapper)
            model = builder.insert_task(task)

            # ID should be available immediately after flush
            assert model.id is not None
            assert model.id == 1

    def test_insert_task_does_not_commit(self):
        """Test that insert_task does not commit the transaction."""
        task = Task(
            id=1,
            name="Test Task",
            priority=5,
            status=TaskStatus.PENDING,
            tags=[],
        )

        with self.Session() as session:
            builder = TaskInsertBuilder(session, self.mapper)
            builder.insert_task(task)
            # Don't commit

        # Task should not be persisted without commit
        with self.Session() as session:
            stmt = select(TaskModel)
            models = session.scalars(stmt).all()
            assert len(models) == 0

    def test_insert_task_commits_when_session_commits(self):
        """Test that insert_task persists when session commits."""
        task = Task(
            id=1,
            name="Test Task",
            priority=5,
            status=TaskStatus.PENDING,
            tags=[],
        )

        with self.Session() as session:
            builder = TaskInsertBuilder(session, self.mapper)
            builder.insert_task(task)
            session.commit()

        # Task should be persisted after commit
        with self.Session() as session:
            stmt = select(TaskModel)
            models = session.scalars(stmt).all()
            assert len(models) == 1
            assert models[0].name == "Test Task"

    def test_insert_task_preserves_all_fields(self):
        """Test that insert_task preserves all task fields."""
        now = datetime.now()
        task = Task(
            id=1,
            name="Complete Task",
            priority=5,
            status=TaskStatus.IN_PROGRESS,
            planned_start=now,
            planned_end=now,
            deadline=now,
            estimated_duration=10.0,
            is_fixed=True,
            depends_on=[2, 3],
            tags=["urgent", "bug"],
        )

        with self.Session() as session:
            builder = TaskInsertBuilder(session, self.mapper)
            model = builder.insert_task(task)

            # Verify all fields are preserved
            assert model.name == "Complete Task"
            assert model.priority == 5
            assert model.status == "IN_PROGRESS"
            assert model.estimated_duration == 10.0
            assert model.is_fixed is True
            # Note: tags and depends_on are handled separately
