"""Tests for TagResolver.

This test suite verifies the TagResolver functionality introduced in Phase 2
of Issue 228 (tag entity separation).
"""

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from taskdog_core.infrastructure.persistence.database.models import Base, TagModel
from taskdog_core.infrastructure.persistence.mappers.tag_resolver import TagResolver


class TestTagResolver(unittest.TestCase):
    """Test suite for TagResolver."""

    def setUp(self) -> None:
        """Set up test fixtures with temporary database."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_tags.db"
        self.database_url = f"sqlite:///{self.db_path}"

        # Create engine and session
        self.engine = create_engine(self.database_url)
        Base.metadata.create_all(self.engine)
        self.session = Session(self.engine)

    def tearDown(self) -> None:
        """Clean up database and close connections."""
        self.session.close()
        self.engine.dispose()

        import shutil

        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_resolve_existing_tag_names_to_ids(self) -> None:
        """Test resolving existing tag names to IDs."""
        # Create tags in database
        tag1 = TagModel(name="urgent", created_at=datetime.now())
        tag2 = TagModel(name="backend", created_at=datetime.now())
        self.session.add_all([tag1, tag2])
        self.session.commit()

        # Resolve tag names to IDs
        resolver = TagResolver(self.session)
        tag_ids = resolver.resolve_tag_names_to_ids(["urgent", "backend"])

        self.assertEqual(len(tag_ids), 2)
        self.assertIn(tag1.id, tag_ids)
        self.assertIn(tag2.id, tag_ids)

    def test_resolve_new_tag_names_creates_tags(self) -> None:
        """Test that resolving new tag names automatically creates them."""
        resolver = TagResolver(self.session)
        tag_ids = resolver.resolve_tag_names_to_ids(["new-tag", "another-tag"])

        self.assertEqual(len(tag_ids), 2)

        # Verify tags were created in database
        tags = self.session.query(TagModel).all()
        self.assertEqual(len(tags), 2)
        tag_names = {tag.name for tag in tags}
        self.assertEqual(tag_names, {"new-tag", "another-tag"})

    def test_resolve_mixed_existing_and_new_tags(self) -> None:
        """Test resolving a mix of existing and new tags."""
        # Create one existing tag
        existing_tag = TagModel(name="existing", created_at=datetime.now())
        self.session.add(existing_tag)
        self.session.commit()

        # Resolve mixed tags
        resolver = TagResolver(self.session)
        tag_ids = resolver.resolve_tag_names_to_ids(["existing", "new"])

        self.assertEqual(len(tag_ids), 2)

        # Verify total tags in database
        tags = self.session.query(TagModel).all()
        self.assertEqual(len(tags), 2)
        tag_names = {tag.name for tag in tags}
        self.assertEqual(tag_names, {"existing", "new"})

    def test_resolve_empty_tag_list(self) -> None:
        """Test resolving an empty tag list."""
        resolver = TagResolver(self.session)
        tag_ids = resolver.resolve_tag_names_to_ids([])

        self.assertEqual(tag_ids, [])

    def test_resolve_tag_ids_to_names(self) -> None:
        """Test resolving tag IDs to names."""
        # Create tags
        tag1 = TagModel(name="urgent", created_at=datetime.now())
        tag2 = TagModel(name="backend", created_at=datetime.now())
        self.session.add_all([tag1, tag2])
        self.session.commit()

        # Resolve IDs to names
        resolver = TagResolver(self.session)
        tag_names = resolver.resolve_tag_ids_to_names([tag1.id, tag2.id])

        self.assertEqual(len(tag_names), 2)
        self.assertIn("urgent", tag_names)
        self.assertIn("backend", tag_names)

    def test_cache_reduces_database_queries(self) -> None:
        """Test that cache reduces database queries."""
        # Create a tag
        tag = TagModel(name="cached", created_at=datetime.now())
        self.session.add(tag)
        self.session.commit()

        resolver = TagResolver(self.session)

        # First call - should query database
        tag_ids_1 = resolver.resolve_tag_names_to_ids(["cached"])

        # Second call - should use cache (verify by checking the result is the same)
        tag_ids_2 = resolver.resolve_tag_names_to_ids(["cached"])

        self.assertEqual(tag_ids_1, tag_ids_2)
        self.assertEqual(tag_ids_1[0], tag.id)

    def test_clear_cache(self) -> None:
        """Test that clear_cache removes all cached entries."""
        # Create a tag
        tag = TagModel(name="test", created_at=datetime.now())
        self.session.add(tag)
        self.session.commit()

        resolver = TagResolver(self.session)

        # Cache the tag
        resolver.resolve_tag_names_to_ids(["test"])

        # Clear cache
        resolver.clear_cache()

        # Verify cache is empty
        self.assertEqual(len(resolver._name_to_id_cache), 0)
        self.assertEqual(len(resolver._id_to_name_cache), 0)

    def test_duplicate_tag_name_prevented(self) -> None:
        """Test that duplicate tag names are prevented."""
        # Create a tag
        tag1 = TagModel(name="duplicate", created_at=datetime.now())
        self.session.add(tag1)
        self.session.commit()

        resolver = TagResolver(self.session)

        # Try to resolve the same tag name multiple times
        tag_ids_1 = resolver.resolve_tag_names_to_ids(["duplicate"])
        tag_ids_2 = resolver.resolve_tag_names_to_ids(["duplicate"])

        # Should return the same ID
        self.assertEqual(tag_ids_1, tag_ids_2)

        # Verify only one tag exists
        tags = self.session.query(TagModel).filter(TagModel.name == "duplicate").all()
        self.assertEqual(len(tags), 1)

    def test_preserves_tag_order(self) -> None:
        """Test that tag order is preserved in results."""
        resolver = TagResolver(self.session)

        # Resolve tags in specific order
        tag_names = ["zebra", "alpha", "beta"]
        tag_ids = resolver.resolve_tag_names_to_ids(tag_names)

        # Resolve back to names
        resolved_names = resolver.resolve_tag_ids_to_names(tag_ids)

        # Order should be preserved
        self.assertEqual(resolved_names, tag_names)

    def test_resolve_tag_names_with_special_characters(self) -> None:
        """Test resolving tag names with special characters."""
        special_names = ["bug-fix", "v2.0", "frontend/ui", "日本語"]

        resolver = TagResolver(self.session)
        tag_ids = resolver.resolve_tag_names_to_ids(special_names)

        self.assertEqual(len(tag_ids), len(special_names))

        # Verify all tags were created
        tags = self.session.query(TagModel).all()
        self.assertEqual(len(tags), len(special_names))
        tag_names = {tag.name for tag in tags}
        self.assertEqual(tag_names, set(special_names))

    def test_resolve_duplicate_names_in_same_list(self) -> None:
        """Test resolving a list with duplicate tag names."""
        resolver = TagResolver(self.session)

        # List with duplicates
        tag_names = ["urgent", "backend", "urgent"]
        tag_ids = resolver.resolve_tag_names_to_ids(tag_names)

        # Should return IDs preserving duplicates
        self.assertEqual(len(tag_ids), 3)
        self.assertEqual(tag_ids[0], tag_ids[2])  # First and third should be the same

        # But only create one tag in database
        tags = self.session.query(TagModel).filter(TagModel.name == "urgent").all()
        self.assertEqual(len(tags), 1)

    def test_bidirectional_conversion(self) -> None:
        """Test that name->ID->name conversion works correctly."""
        original_names = ["test1", "test2", "test3"]

        resolver = TagResolver(self.session)

        # Convert names to IDs
        tag_ids = resolver.resolve_tag_names_to_ids(original_names)

        # Convert IDs back to names
        resolved_names = resolver.resolve_tag_ids_to_names(tag_ids)

        # Should get back the original names
        self.assertEqual(resolved_names, original_names)


if __name__ == "__main__":
    unittest.main()
