"""Unit tests for TaskTagRelationshipBuilder."""

import unittest
from datetime import datetime

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from taskdog_core.infrastructure.persistence.database.models import (
    TagModel,
    TaskModel,
    TaskTagModel,
)
from taskdog_core.infrastructure.persistence.database.models.task_model import Base
from taskdog_core.infrastructure.persistence.database.mutation_builders import (
    TaskTagRelationshipBuilder,
)
from taskdog_core.infrastructure.persistence.mappers.tag_resolver import TagResolver


class TestTaskTagRelationshipBuilder(unittest.TestCase):
    """Test cases for TaskTagRelationshipBuilder."""

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

    def test_sync_task_tags_adds_new_tags(self):
        """Test that sync_task_tags adds new tags to task."""
        # Create initial task with no tags
        task_model = TaskModel(
            id=1,
            name="Task",
            priority=5,
            status="PENDING",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        with self.Session() as session:
            session.add(task_model)
            session.flush()

            tag_resolver = TagResolver(session)
            builder = TaskTagRelationshipBuilder(session, tag_resolver)
            builder.sync_task_tags(task_model, ["urgent", "backend"])

            # Tags should be added
            self.assertEqual(len(task_model.tag_models), 2)
            tag_names = [tag.name for tag in task_model.tag_models]
            self.assertIn("urgent", tag_names)
            self.assertIn("backend", tag_names)

    def test_sync_task_tags_clears_existing_tags(self):
        """Test that sync_task_tags clears existing tags before adding new ones."""
        with self.Session() as session:
            # Create tags
            tag1 = TagModel(name="urgent", created_at=datetime.now())
            tag2 = TagModel(name="backend", created_at=datetime.now())
            tag3 = TagModel(name="frontend", created_at=datetime.now())
            session.add_all([tag1, tag2, tag3])
            session.flush()

            # Create task with initial tags
            task_model = TaskModel(
                id=1,
                name="Task",
                priority=5,
                status="PENDING",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            task_model.tag_models.extend([tag1, tag2])
            session.add(task_model)
            session.flush()

            # Verify initial tags
            self.assertEqual(len(task_model.tag_models), 2)

            # Sync with different tags
            tag_resolver = TagResolver(session)
            builder = TaskTagRelationshipBuilder(session, tag_resolver)
            builder.sync_task_tags(task_model, ["frontend"])

            # Old tags should be cleared, new tag added
            self.assertEqual(len(task_model.tag_models), 1)
            self.assertEqual(task_model.tag_models[0].name, "frontend")

    def test_sync_task_tags_with_empty_list_clears_all(self):
        """Test that sync_task_tags with empty list clears all tags."""
        with self.Session() as session:
            # Create tags
            tag1 = TagModel(name="urgent", created_at=datetime.now())
            tag2 = TagModel(name="backend", created_at=datetime.now())
            session.add_all([tag1, tag2])
            session.flush()

            # Create task with tags
            task_model = TaskModel(
                id=1,
                name="Task",
                priority=5,
                status="PENDING",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            task_model.tag_models.extend([tag1, tag2])
            session.add(task_model)
            session.flush()

            # Verify initial tags
            self.assertEqual(len(task_model.tag_models), 2)

            # Sync with empty list
            tag_resolver = TagResolver(session)
            builder = TaskTagRelationshipBuilder(session, tag_resolver)
            builder.sync_task_tags(task_model, [])

            # All tags should be cleared
            self.assertEqual(len(task_model.tag_models), 0)

    def test_sync_task_tags_preserves_tag_order(self):
        """Test that sync_task_tags preserves the order of tags."""
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

            tag_resolver = TagResolver(session)
            builder = TaskTagRelationshipBuilder(session, tag_resolver)
            builder.sync_task_tags(task_model, ["zebra", "alpha", "beta", "gamma"])

            # Tags should be in the order specified
            tag_names = [tag.name for tag in task_model.tag_models]
            self.assertEqual(tag_names, ["zebra", "alpha", "beta", "gamma"])

    def test_sync_task_tags_creates_new_tags(self):
        """Test that sync_task_tags creates new tags if they don't exist."""
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

            # Verify no tags exist
            stmt = select(TagModel)
            existing_tags = session.scalars(stmt).all()
            self.assertEqual(len(existing_tags), 0)

            # Sync with new tags
            tag_resolver = TagResolver(session)
            builder = TaskTagRelationshipBuilder(session, tag_resolver)
            builder.sync_task_tags(task_model, ["urgent", "backend"])
            session.commit()

            # Tags should be created
            stmt = select(TagModel)
            created_tags = session.scalars(stmt).all()
            self.assertEqual(len(created_tags), 2)

    def test_sync_task_tags_reuses_existing_tags(self):
        """Test that sync_task_tags reuses existing tags instead of creating duplicates."""
        with self.Session() as session:
            # Create initial tags
            tag1 = TagModel(name="urgent", created_at=datetime.now())
            tag2 = TagModel(name="backend", created_at=datetime.now())
            session.add_all([tag1, tag2])
            session.commit()

            # Create task
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

            # Sync with existing tags
            tag_resolver = TagResolver(session)
            builder = TaskTagRelationshipBuilder(session, tag_resolver)
            builder.sync_task_tags(task_model, ["urgent", "backend"])
            session.commit()

            # Should still only have 2 tags in database
            stmt = select(TagModel)
            all_tags = session.scalars(stmt).all()
            self.assertEqual(len(all_tags), 2)

    def test_sync_task_tags_handles_mixed_new_and_existing_tags(self):
        """Test that sync_task_tags handles mix of new and existing tags."""
        with self.Session() as session:
            # Create one existing tag
            tag1 = TagModel(name="urgent", created_at=datetime.now())
            session.add(tag1)
            session.commit()

            # Create task
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

            # Sync with mix of existing and new tags
            tag_resolver = TagResolver(session)
            builder = TaskTagRelationshipBuilder(session, tag_resolver)
            builder.sync_task_tags(task_model, ["urgent", "backend", "frontend"])
            session.commit()

            # Task should have 3 tags
            self.assertEqual(len(task_model.tag_models), 3)

            # Database should have 3 tags total
            stmt = select(TagModel)
            all_tags = session.scalars(stmt).all()
            self.assertEqual(len(all_tags), 3)

    def test_sync_task_tags_does_not_commit(self):
        """Test that sync_task_tags does not commit the transaction."""
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
            tag_resolver = TagResolver(session)
            builder = TaskTagRelationshipBuilder(session, tag_resolver)
            builder.sync_task_tags(task_model, ["urgent"])
            # Don't commit

        # Tags should not be persisted without commit
        with self.Session() as session:
            task_model = session.get(TaskModel, 1)
            self.assertEqual(len(task_model.tag_models), 0)

    def test_sync_task_tags_persists_on_commit(self):
        """Test that sync_task_tags persists when session commits."""
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

            tag_resolver = TagResolver(session)
            builder = TaskTagRelationshipBuilder(session, tag_resolver)
            builder.sync_task_tags(task_model, ["urgent", "backend"])
            session.commit()

        # Tags should be persisted after commit
        with self.Session() as session:
            task_model = session.get(TaskModel, 1)
            self.assertEqual(len(task_model.tag_models), 2)
            tag_names = [tag.name for tag in task_model.tag_models]
            self.assertIn("urgent", tag_names)
            self.assertIn("backend", tag_names)

    def test_sync_task_tags_creates_task_tag_relationships(self):
        """Test that sync_task_tags creates proper task_tags relationships."""
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

            tag_resolver = TagResolver(session)
            builder = TaskTagRelationshipBuilder(session, tag_resolver)
            builder.sync_task_tags(task_model, ["urgent", "backend"])
            session.commit()

        # Verify task_tags relationships
        with self.Session() as session:
            stmt = select(TaskTagModel)
            relationships = session.scalars(stmt).all()
            self.assertEqual(len(relationships), 2)

            # All relationships should be for task_id=1
            for rel in relationships:
                self.assertEqual(rel.task_id, 1)


if __name__ == "__main__":
    unittest.main()
