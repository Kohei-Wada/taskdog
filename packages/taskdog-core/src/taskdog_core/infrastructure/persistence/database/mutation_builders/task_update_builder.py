"""Builder for UPDATE operations on Task entities.

This builder handles updates to existing task records in the database,
applying changes from Task entities to TaskModel ORM objects.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from taskdog_core.domain.entities.task import Task
from taskdog_core.domain.exceptions.task_exceptions import ConcurrencyConflictError
from taskdog_core.infrastructure.persistence.database.models import TaskModel
from taskdog_core.infrastructure.persistence.mappers.task_db_mapper import TaskDbMapper


class TaskUpdateBuilder:
    """Builder for updating existing Task entities in the database.

    This builder handles UPDATE operations, applying changes from Task
    domain entities to existing TaskModel ORM objects.

    Example:
        >>> mapper = TaskDbMapper()
        >>> builder = TaskUpdateBuilder(session, mapper)
        >>> existing_model = session.get(TaskModel, task.id)
        >>> builder.update_task(existing_model, updated_task)
        >>> # Model is updated in session, commit to persist
    """

    def __init__(self, session: Session, mapper: TaskDbMapper):
        """Initialize the builder.

        Args:
            session: SQLAlchemy session for database operations
            mapper: TaskDbMapper for entity-to-model conversion
        """
        self._session = session
        self._mapper = mapper

    def update_task(self, model: TaskModel, task: Task) -> None:
        """Update an existing task model with Task entity data.

        Args:
            model: Existing TaskModel ORM object to update
            task: Task entity with updated data

        Note:
            - Updates the model in-place
            - Automatically sets updated_at timestamp
            - Bumps the optimistic-lock version, rejecting stale writes
            - Changes are tracked by SQLAlchemy session but not committed
            - Call session.commit() to persist the change

        Raises:
            ConcurrencyConflictError: If ``model`` (freshly loaded from the
                database) is at a newer version than the entity being saved,
                i.e. another writer modified the task in between.
        """
        # Optimistic lock: the model is loaded fresh from the DB, so its version
        # reflects the current row; task.version is what the caller read. A
        # mismatch means someone else wrote first -> reject instead of clobber.
        if model.version != task.version:
            raise ConcurrencyConflictError(
                task_id=model.id,
                expected_version=task.version,
                actual_version=model.version,
            )
        self._mapper.update_model(model, task)
        model.updated_at = datetime.now()
        new_version = task.version + 1
        model.version = new_version
        # Advance the in-memory entity too, so saving the same entity again in
        # the same flow does not conflict against the row it just wrote.
        task.version = new_version
