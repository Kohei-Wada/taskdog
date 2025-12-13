"""TagResolver for converting between tag names and IDs.

This module provides the TagResolver class which handles the conversion between
tag names and tag IDs, with automatic tag creation and caching for performance.

This is part of Phase 2 implementation for Issue 228 (tag entity separation).
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from taskdog_core.infrastructure.persistence.database.models import TagModel


class TagResolver:
    """Resolves tag names to IDs and vice versa with caching.

    This class handles the conversion between tag names (used in the domain layer)
    and tag IDs (used in the database layer). It automatically creates new tags
    when needed and caches results for performance.

    The cache is scoped to the TagResolver instance, which should be created per
    database session.

    Example:
        >>> with session_factory() as session:
        ...     resolver = TagResolver(session)
        ...     tag_ids = resolver.resolve_tag_names_to_ids(["urgent", "backend"])
        ...     # tag_ids = [1, 2] (creates tags if they don't exist)
    """

    def __init__(self, session: Session):
        """Initialize TagResolver with a database session.

        Args:
            session: SQLAlchemy session for database operations
        """
        self._session = session
        self._name_to_id_cache: dict[str, int] = {}
        self._id_to_name_cache: dict[int, str] = {}

    def resolve_tag_names_to_ids(self, tag_names: list[str]) -> list[int]:
        """Convert tag names to tag IDs, creating new tags if needed.

        This method looks up tag IDs for the given tag names. If a tag doesn't
        exist in the database, it creates a new one automatically.

        Args:
            tag_names: List of tag names (e.g., ["urgent", "backend"])

        Returns:
            List of tag IDs corresponding to the tag names (e.g., [1, 2])

        Example:
            >>> resolver.resolve_tag_names_to_ids(["urgent", "backend"])
            [1, 2]
        """
        if not tag_names:
            return []

        # Get unique names that need to be resolved (preserving order for uncached)
        uncached_names = []
        seen = set()
        for name in tag_names:
            if name not in self._name_to_id_cache and name not in seen:
                uncached_names.append(name)
                seen.add(name)

        if not uncached_names:
            # All names are cached, return in original order
            return [self._name_to_id_cache[name] for name in tag_names]

        # Query database for uncached tags
        # Note: SQLAlchemy's Mapped type system has limitations with class attribute access
        # mypy cannot infer that TagModel.name is an InstrumentedAttribute with .in_() method
        stmt = select(TagModel).where(TagModel.name.in_(uncached_names))  # type: ignore[attr-defined]
        existing_tags = self._session.scalars(stmt).all()

        # Update cache with existing tags
        existing_names = set()
        for tag in existing_tags:
            self._name_to_id_cache[tag.name] = tag.id
            self._id_to_name_cache[tag.id] = tag.name
            existing_names.add(tag.name)

        # Create new tags for names that don't exist (no duplicates)
        new_names = [name for name in uncached_names if name not in existing_names]
        for name in new_names:
            new_tag = TagModel(name=name, created_at=datetime.now())
            self._session.add(new_tag)
            self._session.flush()  # Get the ID immediately

            # Update cache
            # After flush(), ID is guaranteed to be set for autoincrement primary key
            assert new_tag.id is not None, "Tag ID should be set after flush()"
            self._name_to_id_cache[name] = new_tag.id
            self._id_to_name_cache[new_tag.id] = name

        # Preserve the original order (including duplicates)
        return [self._name_to_id_cache[name] for name in tag_names]
