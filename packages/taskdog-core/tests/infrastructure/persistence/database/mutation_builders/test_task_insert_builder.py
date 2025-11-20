"""Unit tests for TaskInsertBuilder."""

import unittest
from datetime import datetime

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.infrastructure.persistence.database.models import TaskModel
from taskdog_core.infrastructure.persistence.database.models.task_model import Base
from taskdog_core.infrastructure.persistence.database.mutation_builders import (
    TaskInsertBuilder,
)
from taskdog_core.infrastructure.persistence.mappers.task_db_mapper import TaskDbMapper


class TestTaskInsertBuilder(unittest.TestCase):
    """Test cases for TaskInsertBuilder."""

    def setUp(self):
        """Set up test database and builder."""
        # Create in-memory SQLite database
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.mapper = TaskDbMapper()

    def tearDown(self):
        """Clean up test database."""
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
            self.assertIsInstance(model, TaskModel)
            self.assertEqual(model.name, "Test Task")
            self.assertEqual(model.priority, 5)
            self.assertEqual(model.status, "PENDING")

            # Model should be in session
            self.assertIn(model, session)

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
            self.assertIsNotNone(model.id)
            self.assertEqual(model.id, 1)

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
            self.assertEqual(len(models), 0)

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
            self.assertEqual(len(models), 1)
            self.assertEqual(models[0].name, "Test Task")

    def test_insert_tasks_bulk_creates_multiple_models(self):
        """Test that insert_tasks_bulk creates multiple TaskModels."""
        tasks = [
            Task(id=1, name="Task 1", priority=5, status=TaskStatus.PENDING, tags=[]),
            Task(id=2, name="Task 2", priority=3, status=TaskStatus.PENDING, tags=[]),
            Task(id=3, name="Task 3", priority=1, status=TaskStatus.PENDING, tags=[]),
        ]

        with self.Session() as session:
            builder = TaskInsertBuilder(session, self.mapper)
            models = builder.insert_tasks_bulk(tasks)

            # Should return 3 models
            self.assertEqual(len(models), 3)
            self.assertEqual(models[0].name, "Task 1")
            self.assertEqual(models[1].name, "Task 2")
            self.assertEqual(models[2].name, "Task 3")

            # All models should be in session
            for model in models:
                self.assertIn(model, session)

    def test_insert_tasks_bulk_flushes_for_ids(self):
        """Test that insert_tasks_bulk flushes to get IDs immediately."""
        tasks = [
            Task(id=1, name="Task 1", priority=5, status=TaskStatus.PENDING, tags=[]),
            Task(id=2, name="Task 2", priority=3, status=TaskStatus.PENDING, tags=[]),
        ]

        with self.Session() as session:
            builder = TaskInsertBuilder(session, self.mapper)
            models = builder.insert_tasks_bulk(tasks)

            # All IDs should be available immediately
            self.assertEqual(models[0].id, 1)
            self.assertEqual(models[1].id, 2)

    def test_insert_tasks_bulk_with_empty_list(self):
        """Test that insert_tasks_bulk handles empty list."""
        tasks = []

        with self.Session() as session:
            builder = TaskInsertBuilder(session, self.mapper)
            models = builder.insert_tasks_bulk(tasks)

            # Should return empty list
            self.assertEqual(len(models), 0)

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
            self.assertEqual(model.name, "Complete Task")
            self.assertEqual(model.priority, 5)
            self.assertEqual(model.status, "IN_PROGRESS")
            self.assertEqual(model.estimated_duration, 10.0)
            self.assertEqual(model.is_fixed, True)
            # Note: tags and depends_on are handled separately


if __name__ == "__main__":
    unittest.main()
