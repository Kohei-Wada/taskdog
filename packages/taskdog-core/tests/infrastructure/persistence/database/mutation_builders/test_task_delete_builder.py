"""Unit tests for TaskDeleteBuilder."""

import unittest
from datetime import datetime

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from taskdog_core.infrastructure.persistence.database.models import TaskModel
from taskdog_core.infrastructure.persistence.database.models.task_model import Base
from taskdog_core.infrastructure.persistence.database.mutation_builders import (
    TaskDeleteBuilder,
)


class TestTaskDeleteBuilder(unittest.TestCase):
    """Test cases for TaskDeleteBuilder."""

    def setUp(self):
        """Set up test database and builder."""
        # Create in-memory SQLite database
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def tearDown(self):
        """Clean up test database."""
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
            self.assertTrue(result)

        # Task should be deleted
        with self.Session() as session:
            stmt = select(TaskModel)
            models = session.scalars(stmt).all()
            self.assertEqual(len(models), 0)

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

            self.assertTrue(result)

    def test_delete_task_returns_false_when_not_found(self):
        """Test that delete_task returns False when task doesn't exist."""
        with self.Session() as session:
            builder = TaskDeleteBuilder(session)
            result = builder.delete_task(999)

            # Should return False for nonexistent task
            self.assertFalse(result)

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
            self.assertEqual(len(models), 1)

    def test_delete_tasks_bulk_deletes_multiple_tasks(self):
        """Test that delete_tasks_bulk deletes multiple tasks."""
        # Create initial models
        models = [
            TaskModel(
                id=1,
                name="Task 1",
                priority=5,
                status="PENDING",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            TaskModel(
                id=2,
                name="Task 2",
                priority=3,
                status="PENDING",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            TaskModel(
                id=3,
                name="Task 3",
                priority=1,
                status="PENDING",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
        ]

        with self.Session() as session:
            for model in models:
                session.add(model)
            session.commit()

        with self.Session() as session:
            builder = TaskDeleteBuilder(session)
            count = builder.delete_tasks_bulk([1, 2, 3])
            session.commit()

            # Should return count of deleted tasks
            self.assertEqual(count, 3)

        # All tasks should be deleted
        with self.Session() as session:
            stmt = select(TaskModel)
            models = session.scalars(stmt).all()
            self.assertEqual(len(models), 0)

    def test_delete_tasks_bulk_returns_count_of_deleted(self):
        """Test that delete_tasks_bulk returns correct count."""
        # Create only 2 tasks
        models = [
            TaskModel(
                id=1,
                name="Task 1",
                priority=5,
                status="PENDING",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            TaskModel(
                id=2,
                name="Task 2",
                priority=3,
                status="PENDING",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
        ]

        with self.Session() as session:
            for model in models:
                session.add(model)
            session.commit()

        with self.Session() as session:
            builder = TaskDeleteBuilder(session)
            # Try to delete 3 tasks, but only 2 exist
            count = builder.delete_tasks_bulk([1, 2, 999])

            # Should only count the 2 that existed
            self.assertEqual(count, 2)

    def test_delete_tasks_bulk_with_empty_list(self):
        """Test that delete_tasks_bulk handles empty list."""
        with self.Session() as session:
            builder = TaskDeleteBuilder(session)
            count = builder.delete_tasks_bulk([])

            # Should return 0
            self.assertEqual(count, 0)

    def test_delete_tasks_bulk_skips_nonexistent_ids(self):
        """Test that delete_tasks_bulk skips nonexistent IDs."""
        # Create only task 1
        initial_model = TaskModel(
            id=1,
            name="Task 1",
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
            # Try to delete 1, 2, 3 but only 1 exists
            count = builder.delete_tasks_bulk([1, 2, 3])
            session.commit()

            # Should only delete 1 task
            self.assertEqual(count, 1)

        # Only task 1 should be deleted, others never existed
        with self.Session() as session:
            stmt = select(TaskModel)
            models = session.scalars(stmt).all()
            self.assertEqual(len(models), 0)

    def test_delete_tasks_bulk_does_not_commit(self):
        """Test that delete_tasks_bulk does not commit the transaction."""
        models = [
            TaskModel(
                id=1,
                name="Task 1",
                priority=5,
                status="PENDING",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            TaskModel(
                id=2,
                name="Task 2",
                priority=3,
                status="PENDING",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
        ]

        with self.Session() as session:
            for model in models:
                session.add(model)
            session.commit()

        with self.Session() as session:
            builder = TaskDeleteBuilder(session)
            builder.delete_tasks_bulk([1, 2])
            # Don't commit

        # Tasks should still exist without commit
        with self.Session() as session:
            stmt = select(TaskModel)
            models = session.scalars(stmt).all()
            self.assertEqual(len(models), 2)


if __name__ == "__main__":
    unittest.main()
