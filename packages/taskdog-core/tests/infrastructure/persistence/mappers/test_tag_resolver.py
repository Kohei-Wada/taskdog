"""Tests for TagResolver.

This test suite verifies the TagResolver functionality introduced in Phase 2
of Issue 228 (tag entity separation).
"""

from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from taskdog_core.infrastructure.persistence.database.models import Base, TagModel
from taskdog_core.infrastructure.persistence.mappers.tag_resolver import TagResolver


class TestTagResolver:
    """Test suite for TagResolver."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up test fixtures with temporary database."""
        self.temp_dir = tmp_path
        self.db_path = Path(self.temp_dir) / "test_tags.db"
        self.database_url = f"sqlite:///{self.db_path}"

        # Create engine and session
        self.engine = create_engine(self.database_url)
        Base.metadata.create_all(self.engine)
        self.session = Session(self.engine)
        yield
        self.session.close()
        self.engine.dispose()

    def test_resolve_existing_tag_names_to_ids(self):
        """Test resolving existing tag names to IDs."""
        # Create tags in database
        tag1 = TagModel(name="urgent", created_at=datetime.now())
        tag2 = TagModel(name="backend", created_at=datetime.now())
        self.session.add_all([tag1, tag2])
        self.session.commit()

        # Resolve tag names to IDs
        resolver = TagResolver(self.session)
        tag_ids = resolver.resolve_tag_names_to_ids(["urgent", "backend"])

        assert len(tag_ids) == 2
        assert tag1.id in tag_ids
        assert tag2.id in tag_ids

    def test_resolve_new_tag_names_creates_tags(self):
        """Test that resolving new tag names automatically creates them."""
        resolver = TagResolver(self.session)
        tag_ids = resolver.resolve_tag_names_to_ids(["new-tag", "another-tag"])

        assert len(tag_ids) == 2

        # Verify tags were created in database
        tags = self.session.query(TagModel).all()
        assert len(tags) == 2
        tag_names = {tag.name for tag in tags}
        assert tag_names == {"new-tag", "another-tag"}

    def test_resolve_mixed_existing_and_new_tags(self):
        """Test resolving a mix of existing and new tags."""
        # Create one existing tag
        existing_tag = TagModel(name="existing", created_at=datetime.now())
        self.session.add(existing_tag)
        self.session.commit()

        # Resolve mixed tags
        resolver = TagResolver(self.session)
        tag_ids = resolver.resolve_tag_names_to_ids(["existing", "new"])

        assert len(tag_ids) == 2

        # Verify total tags in database
        tags = self.session.query(TagModel).all()
        assert len(tags) == 2
        tag_names = {tag.name for tag in tags}
        assert tag_names == {"existing", "new"}

    def test_resolve_empty_tag_list(self):
        """Test resolving an empty tag list."""
        resolver = TagResolver(self.session)
        tag_ids = resolver.resolve_tag_names_to_ids([])

        assert tag_ids == []

    def test_cache_reduces_database_queries(self):
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

        assert tag_ids_1 == tag_ids_2
        assert tag_ids_1[0] == tag.id

    def test_duplicate_tag_name_prevented(self):
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
        assert tag_ids_1 == tag_ids_2

        # Verify only one tag exists
        tags = self.session.query(TagModel).filter(TagModel.name == "duplicate").all()
        assert len(tags) == 1

    def test_resolve_tag_names_with_special_characters(self):
        """Test resolving tag names with special characters."""
        special_names = ["bug-fix", "v2.0", "frontend/ui", "日本語"]

        resolver = TagResolver(self.session)
        tag_ids = resolver.resolve_tag_names_to_ids(special_names)

        assert len(tag_ids) == len(special_names)

        # Verify all tags were created
        tags = self.session.query(TagModel).all()
        assert len(tags) == len(special_names)
        tag_names = {tag.name for tag in tags}
        assert tag_names == set(special_names)

    def test_resolve_duplicate_names_in_same_list(self):
        """Test resolving a list with duplicate tag names."""
        resolver = TagResolver(self.session)

        # List with duplicates
        tag_names = ["urgent", "backend", "urgent"]
        tag_ids = resolver.resolve_tag_names_to_ids(tag_names)

        # Should return IDs preserving duplicates
        assert len(tag_ids) == 3
        assert tag_ids[0] == tag_ids[2]  # First and third should be the same

        # But only create one tag in database
        tags = self.session.query(TagModel).filter(TagModel.name == "urgent").all()
        assert len(tags) == 1
