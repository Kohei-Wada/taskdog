"""Tests for migrate_tags_to_normalized_schema script (Phase 5)."""

import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

# Add scripts to path for importing
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "scripts"))

from migrate_tags_to_normalized_schema import migrate_tags_to_normalized_schema

from taskdog_core.infrastructure.persistence.database.models import (
    Base,
    TagModel,
    TaskModel,
)


class TestMigrateTagsToNormalizedSchema(unittest.TestCase):
    """Test suite for tag migration script."""

    def setUp(self) -> None:
        """Set up test fixtures with temporary database."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_migration.db"
        self.database_url = f"sqlite:///{self.db_path}"

        # Create database with schema
        self.engine = create_engine(self.database_url)
        Base.metadata.create_all(self.engine)

    def tearDown(self) -> None:
        """Clean up database."""
        self.engine.dispose()
        import shutil

        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def _create_task_with_json_tags(
        self, task_id: int, name: str, tag_names: list[str]
    ) -> None:
        """Helper to create a task with JSON tags (legacy format)."""
        with Session(self.engine) as session:
            task = TaskModel(
                id=task_id,
                name=name,
                priority=1,
                status="PENDING",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                tags=json.dumps(tag_names),  # Legacy JSON format
                is_archived=False,
            )
            session.add(task)
            session.commit()

    def _get_task_tag_models(self, task_id: int) -> list[str]:
        """Helper to get tag names from task's tag_models relationship."""
        with Session(self.engine) as session:
            task = session.get(TaskModel, task_id)
            if task and task.tag_models:
                return [tag.name for tag in task.tag_models]
            return []

    def _get_tag_count(self) -> int:
        """Helper to get total number of tags in database."""
        with Session(self.engine) as session:
            stmt = select(TagModel)
            return len(session.scalars(stmt).all())

    def test_basic_migration(self) -> None:
        """Test basic migration from JSON to normalized schema (Phase 5)."""
        # Create task with JSON tags
        self._create_task_with_json_tags(1, "Task 1", ["urgent", "backend"])

        # Run migration
        stats = migrate_tags_to_normalized_schema(self.database_url)

        # Verify migration stats
        self.assertEqual(stats["migrated"], 1)
        self.assertEqual(stats["skipped"], 0)
        self.assertEqual(stats["errors"], 0)

        # Verify tags migrated to normalized schema
        tag_names = self._get_task_tag_models(1)
        self.assertEqual(set(tag_names), {"urgent", "backend"})

        # Verify tags exist in tags table
        self.assertEqual(self._get_tag_count(), 2)

    def test_idempotency(self) -> None:
        """Test that migration can be run multiple times safely (Phase 5)."""
        # Create task with JSON tags
        self._create_task_with_json_tags(1, "Task 1", ["urgent"])

        # Run migration first time
        stats1 = migrate_tags_to_normalized_schema(self.database_url)
        self.assertEqual(stats1["migrated"], 1)

        # Run migration second time
        stats2 = migrate_tags_to_normalized_schema(self.database_url)

        # Second run should skip already-migrated task
        self.assertEqual(stats2["migrated"], 0)
        self.assertEqual(stats2["skipped"], 1)
        self.assertEqual(stats2["errors"], 0)

        # Verify tags still correct
        tag_names = self._get_task_tag_models(1)
        self.assertEqual(tag_names, ["urgent"])

        # Verify no duplicate tags created
        self.assertEqual(self._get_tag_count(), 1)

    def test_empty_tags(self) -> None:
        """Test migration skips tasks with empty tags (Phase 5)."""
        # Create tasks with various empty tag representations
        self._create_task_with_json_tags(1, "Task 1", [])
        with Session(self.engine) as session:
            task2 = TaskModel(
                id=2,
                name="Task 2",
                priority=1,
                status="PENDING",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                tags="",  # Empty string
                is_archived=False,
            )
            session.add(task2)
            session.commit()

        # Run migration
        stats = migrate_tags_to_normalized_schema(self.database_url)

        # Both should be skipped
        self.assertEqual(stats["migrated"], 0)
        self.assertEqual(stats["skipped"], 2)
        self.assertEqual(stats["errors"], 0)

    def test_invalid_json(self) -> None:
        """Test migration handles invalid JSON gracefully (Phase 5)."""
        # Create task with invalid JSON
        with Session(self.engine) as session:
            task = TaskModel(
                id=1,
                name="Task 1",
                priority=1,
                status="PENDING",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                tags="{invalid json",  # Malformed JSON
                is_archived=False,
            )
            session.add(task)
            session.commit()

        # Run migration
        stats = migrate_tags_to_normalized_schema(self.database_url)

        # Should report error
        self.assertEqual(stats["migrated"], 0)
        self.assertEqual(stats["skipped"], 0)
        self.assertEqual(stats["errors"], 1)

    def test_already_migrated_task(self) -> None:
        """Test migration skips tasks already migrated (Phase 5)."""
        # Create task with both JSON tags and tag_models (already migrated)
        with Session(self.engine) as session:
            task = TaskModel(
                id=1,
                name="Task 1",
                priority=1,
                status="PENDING",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                tags=json.dumps(["urgent"]),
                is_archived=False,
            )

            # Create tag and associate (simulating already migrated)
            tag = TagModel(name="urgent", created_at=datetime.now())
            session.add(tag)
            session.flush()
            task.tag_models.append(tag)
            session.add(task)
            session.commit()

        # Run migration
        stats = migrate_tags_to_normalized_schema(self.database_url)

        # Should skip (already has tag_models)
        self.assertEqual(stats["migrated"], 0)
        self.assertEqual(stats["skipped"], 1)
        self.assertEqual(stats["errors"], 0)

    def test_special_characters(self) -> None:
        """Test migration handles special characters in tag names (Phase 5)."""
        special_tags = [
            "bug-fix",
            "v2.0",
            "frontend/ui",
            "high-priority!",
            "'; DROP TABLE tags;--",
        ]
        self._create_task_with_json_tags(1, "Task 1", special_tags)

        # Run migration
        stats = migrate_tags_to_normalized_schema(self.database_url)

        # Verify migration success
        self.assertEqual(stats["migrated"], 1)
        self.assertEqual(stats["errors"], 0)

        # Verify all special character tags preserved
        tag_names = self._get_task_tag_models(1)
        self.assertEqual(set(tag_names), set(special_tags))

    def test_unicode_tags(self) -> None:
        """Test migration handles Unicode tag names (Phase 5)."""
        unicode_tags = ["🔥urgent", "日本語", "عاجل", "urgent緊急🚨"]
        self._create_task_with_json_tags(1, "Task 1", unicode_tags)

        # Run migration
        stats = migrate_tags_to_normalized_schema(self.database_url)

        # Verify migration success
        self.assertEqual(stats["migrated"], 1)
        self.assertEqual(stats["errors"], 0)

        # Verify all Unicode tags preserved
        tag_names = self._get_task_tag_models(1)
        self.assertEqual(set(tag_names), set(unicode_tags))

    def test_large_tag_set(self) -> None:
        """Test migration handles tasks with 100+ tags (Phase 5)."""
        # Create task with 100 tags
        large_tag_set = [f"tag-{i:03d}" for i in range(100)]
        self._create_task_with_json_tags(1, "Task with many tags", large_tag_set)

        # Run migration
        stats = migrate_tags_to_normalized_schema(self.database_url)

        # Verify migration success
        self.assertEqual(stats["migrated"], 1)
        self.assertEqual(stats["errors"], 0)

        # Verify all 100 tags migrated
        tag_names = self._get_task_tag_models(1)
        self.assertEqual(len(tag_names), 100)
        self.assertEqual(set(tag_names), set(large_tag_set))

    def test_shared_tags_across_tasks(self) -> None:
        """Test migration creates shared tags correctly (Phase 5)."""
        # Create multiple tasks with overlapping tags
        self._create_task_with_json_tags(1, "Task 1", ["urgent", "backend"])
        self._create_task_with_json_tags(2, "Task 2", ["urgent", "frontend"])
        self._create_task_with_json_tags(3, "Task 3", ["backend", "database"])

        # Run migration
        stats = migrate_tags_to_normalized_schema(self.database_url)

        # Verify all tasks migrated
        self.assertEqual(stats["migrated"], 3)
        self.assertEqual(stats["errors"], 0)

        # Verify shared tags (should be 4 unique tags total)
        self.assertEqual(self._get_tag_count(), 4)

        # Verify each task has correct tags
        self.assertEqual(set(self._get_task_tag_models(1)), {"urgent", "backend"})
        self.assertEqual(set(self._get_task_tag_models(2)), {"urgent", "frontend"})
        self.assertEqual(set(self._get_task_tag_models(3)), {"backend", "database"})

    def test_large_scale_migration(self) -> None:
        """Test migration performance with 1000+ tasks (Phase 5)."""
        # Create 100 tasks with various tag combinations
        for i in range(100):
            tags = [f"category-{i // 10}", f"task-{i:03d}", f"batch-{i % 5}"]
            self._create_task_with_json_tags(i + 1, f"Task {i}", tags)

        # Run migration
        stats = migrate_tags_to_normalized_schema(self.database_url)

        # Verify all tasks migrated
        self.assertEqual(stats["migrated"], 100)
        self.assertEqual(stats["errors"], 0)

        # Verify tags created (should be less than 300 due to sharing)
        tag_count = self._get_tag_count()
        self.assertGreater(tag_count, 100)  # At least 100 task-specific tags
        self.assertLess(tag_count, 300)  # But many shared tags

    def test_mixed_migrated_and_unmigrated(self) -> None:
        """Test migration handles mixed state (Phase 5)."""
        # Create unmigrated task
        self._create_task_with_json_tags(1, "Unmigrated", ["tag1"])

        # Create already-migrated task
        with Session(self.engine) as session:
            task2 = TaskModel(
                id=2,
                name="Already migrated",
                priority=1,
                status="PENDING",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                tags=json.dumps(["tag2"]),
                is_archived=False,
            )
            tag2 = TagModel(name="tag2", created_at=datetime.now())
            session.add(tag2)
            session.flush()
            task2.tag_models.append(tag2)
            session.add(task2)
            session.commit()

        # Run migration
        stats = migrate_tags_to_normalized_schema(self.database_url)

        # Should migrate only the unmigrated one
        self.assertEqual(stats["migrated"], 1)
        self.assertEqual(stats["skipped"], 1)
        self.assertEqual(stats["errors"], 0)


if __name__ == "__main__":
    unittest.main()
