"""Builder for UPDATE operations on Task entities.

This builder handles updates to existing task records in the database,
applying changes from Task entities to TaskModel ORM objects.
"""

from sqlalchemy.orm import Session

from taskdog_core.domain.entities.task import Task
from taskdog_core.domain.services.time_provider import ITimeProvider
from taskdog_core.infrastructure.persistence.database.models import TaskModel
from taskdog_core.infrastructure.persistence.mappers.task_db_mapper import TaskDbMapper


class TaskUpdateBuilder:
    """Builder for updating existing Task entities in the database.

    This builder handles UPDATE operations, applying changes from Task
    domain entities to existing TaskModel ORM objects.

    Example:
        >>> mapper = TaskDbMapper()
        >>> builder = TaskUpdateBuilder(session, mapper, time_provider)
        >>> existing_model = session.get(TaskModel, task.id)
        >>> builder.update_task(existing_model, updated_task)
        >>> # Model is updated in session, commit to persist
    """

    def __init__(
        self, session: Session, mapper: TaskDbMapper, time_provider: ITimeProvider
    ):
        """Initialize the builder.

        Args:
            session: SQLAlchemy session for database operations
            mapper: TaskDbMapper for entity-to-model conversion
            time_provider: Provider for the updated_at timestamp
        """
        self._session = session
        self._mapper = mapper
        self._time_provider = time_provider

    def update_task(self, model: TaskModel, task: Task) -> None:
        """Update an existing task model with Task entity data.

        Args:
            model: Existing TaskModel ORM object to update
            task: Task entity with updated data

        Note:
            - Updates the model in-place
            - Automatically sets updated_at timestamp
            - Changes are tracked by SQLAlchemy session but not committed
            - Call session.commit() to persist the change
        """
        self._mapper.update_model(model, task)
        model.updated_at = self._time_provider.now()
