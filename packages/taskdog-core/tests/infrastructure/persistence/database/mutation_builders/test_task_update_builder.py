"""Unit tests for TaskUpdateBuilder."""

import unittest
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.infrastructure.persistence.database.models import TaskModel
from taskdog_core.infrastructure.persistence.database.models.task_model import Base
from taskdog_core.infrastructure.persistence.database.mutation_builders import (
    TaskUpdateBuilder,
)
from taskdog_core.infrastructure.persistence.mappers.task_db_mapper import TaskDbMapper


class TestTaskUpdateBuilder(unittest.TestCase):
    """Test cases for TaskUpdateBuilder."""

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
            self.assertEqual(initial_model.name, "New Name")
            self.assertEqual(initial_model.priority, 10)
            self.assertEqual(initial_model.status, "IN_PROGRESS")

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
            self.assertNotEqual(initial_model.updated_at, before_update)
            self.assertGreater(initial_model.updated_at, before_update)

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
            self.assertEqual(model.name, "Old Name")  # Still old value

    def test_update_tasks_bulk_updates_multiple_tasks(self):
        """Test that update_tasks_bulk updates multiple tasks."""
        # Create initial models
        models = {
            1: TaskModel(
                id=1,
                name="Task 1",
                priority=5,
                status="PENDING",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            2: TaskModel(
                id=2,
                name="Task 2",
                priority=3,
                status="PENDING",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
        }

        # Updated tasks
        updated_tasks = [
            Task(
                id=1,
                name="Updated Task 1",
                priority=10,
                status=TaskStatus.PENDING,
                tags=[],
            ),
            Task(
                id=2,
                name="Updated Task 2",
                priority=8,
                status=TaskStatus.PENDING,
                tags=[],
            ),
        ]

        with self.Session() as session:
            for model in models.values():
                session.add(model)
            session.flush()

            builder = TaskUpdateBuilder(session, self.mapper)
            builder.update_tasks_bulk(models, updated_tasks)

            # Verify all updates applied
            self.assertEqual(models[1].name, "Updated Task 1")
            self.assertEqual(models[1].priority, 10)
            self.assertEqual(models[2].name, "Updated Task 2")
            self.assertEqual(models[2].priority, 8)

    def test_update_tasks_bulk_skips_nonexistent_tasks(self):
        """Test that update_tasks_bulk skips tasks not in models dict."""
        # Only model 1 exists
        models = {
            1: TaskModel(
                id=1,
                name="Task 1",
                priority=5,
                status="PENDING",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
        }

        # Try to update both 1 and 2
        updated_tasks = [
            Task(
                id=1,
                name="Updated Task 1",
                priority=10,
                status=TaskStatus.PENDING,
                tags=[],
            ),
            Task(
                id=2,
                name="Updated Task 2",
                priority=8,
                status=TaskStatus.PENDING,
                tags=[],
            ),
        ]

        with self.Session() as session:
            session.add(models[1])
            session.flush()

            builder = TaskUpdateBuilder(session, self.mapper)
            # Should not raise error even though task 2 doesn't exist
            builder.update_tasks_bulk(models, updated_tasks)

            # Only task 1 should be updated
            self.assertEqual(models[1].name, "Updated Task 1")

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
            self.assertEqual(initial_model.name, "Complete Task")
            self.assertEqual(initial_model.priority, 10)
            self.assertEqual(initial_model.status, "IN_PROGRESS")
            self.assertEqual(initial_model.estimated_duration, 15.0)
            self.assertEqual(initial_model.is_fixed, True)

    def test_update_tasks_bulk_with_empty_list(self):
        """Test that update_tasks_bulk handles empty task list."""
        models = {
            1: TaskModel(
                id=1,
                name="Task 1",
                priority=5,
                status="PENDING",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
        }

        updated_tasks = []

        with self.Session() as session:
            session.add(models[1])
            session.flush()

            builder = TaskUpdateBuilder(session, self.mapper)
            # Should not raise error with empty list
            builder.update_tasks_bulk(models, updated_tasks)

            # Original values should remain
            self.assertEqual(models[1].name, "Task 1")


if __name__ == "__main__":
    unittest.main()
