"""Builder for managing task-tag many-to-many relationships.

This builder handles the synchronization of task-tag associations in the
normalized database schema (task_tags junction table).
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from taskdog_core.infrastructure.persistence.database.models import TagModel, TaskModel
from taskdog_core.infrastructure.persistence.mappers.tag_resolver import TagResolver


class TaskTagRelationshipBuilder:
    """Builder for managing task-tag many-to-many relationships.

    This builder provides methods to synchronize task-tag associations,
    handling the task_tags junction table operations. It uses TagResolver
    to manage tag entities and ensures proper order preservation.

    Example:
        >>> tag_resolver = TagResolver(session)
        >>> builder = TaskTagRelationshipBuilder(session, tag_resolver)
        >>> builder.sync_task_tags(task_model, ["urgent", "bug"])
    """

    def __init__(self, session: Session, tag_resolver: TagResolver):
        """Initialize the builder.

        Args:
            session: SQLAlchemy session for database operations
            tag_resolver: TagResolver for tag name/ID conversion and management
        """
        self._session = session
        self._tag_resolver = tag_resolver

    def sync_task_tags(self, task_model: TaskModel, tag_names: list[str]) -> None:
        """Synchronize task's tag relationships (replaces existing tags).

        This method performs a complete replacement of task tags:
        1. Clears all existing tag relationships
        2. If tag_names is empty, stops here
        3. Resolves tag names to IDs (creates new tags if needed)
        4. Fetches TagModel instances
        5. Associates them with the task (preserving original order)

        Args:
            task_model: The TaskModel instance to update
            tag_names: List of tag names for this task (replaces all existing)

        Note:
            - SQLAlchemy automatically handles the task_tags junction table
            - Tag order is preserved (SQL IN clause doesn't guarantee order)
            - Creates new tags if they don't exist (via TagResolver)
            - This is a full replacement, not an append operation
        """
        # Clear existing tag relationships
        task_model.tag_models.clear()  # type: ignore[attr-defined]

        if not tag_names:
            # No tags to associate
            return

        # Resolve tag names to IDs (creates new tags if needed)
        tag_ids = self._tag_resolver.resolve_tag_names_to_ids(tag_names)

        # Fetch TagModel instances and associate with task
        ordered_tag_models = self._fetch_tag_models_ordered(tag_ids)
        task_model.tag_models.extend(ordered_tag_models)  # type: ignore[attr-defined]

    def _fetch_tag_models_ordered(self, tag_ids: list[int]) -> list[TagModel]:
        """Fetch TagModels preserving the specified order.

        Args:
            tag_ids: List of tag IDs in the desired order

        Returns:
            List of TagModel instances in the same order as tag_ids

        Note:
            SQL IN clause doesn't guarantee order, so we manually preserve it
            by sorting the fetched models according to the input tag_ids order.
        """
        # Fetch all tag models (unordered from SQL perspective)
        stmt = select(TagModel).where(TagModel.id.in_(tag_ids))  # type: ignore[attr-defined]
        tag_models_list = self._session.scalars(stmt).all()

        # Create lookup map: ID -> TagModel
        tag_models_by_id = {tag.id: tag for tag in tag_models_list}

        # Return models in the original order
        return [tag_models_by_id[tag_id] for tag_id in tag_ids]
