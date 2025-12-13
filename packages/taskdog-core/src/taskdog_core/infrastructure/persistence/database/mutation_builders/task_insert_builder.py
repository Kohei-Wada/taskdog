"""Builder for INSERT operations on Task entities.

This builder handles the creation of new task records in the database,
converting Task entities to TaskModel ORM objects and managing the
database insert operations.
"""

from sqlalchemy.orm import Session

from taskdog_core.domain.entities.task import Task
from taskdog_core.infrastructure.persistence.database.models import TaskModel
from taskdog_core.infrastructure.persistence.mappers.task_db_mapper import TaskDbMapper


class TaskInsertBuilder:
    """Builder for inserting new Task entities into the database.

    This builder handles INSERT operations, converting Task domain entities
    to TaskModel ORM objects and adding them to the database session.

    Example:
        >>> mapper = TaskDbMapper()
        >>> builder = TaskInsertBuilder(session, mapper)
        >>> model = builder.insert_task(new_task)
        >>> # Task is now in session, flush() to get ID immediately
    """

    def __init__(self, session: Session, mapper: TaskDbMapper):
        """Initialize the builder.

        Args:
            session: SQLAlchemy session for database operations
            mapper: TaskDbMapper for entity-to-model conversion
        """
        self._session = session
        self._mapper = mapper

    def insert_task(self, task: Task) -> TaskModel:
        """Insert a new task into the database.

        Args:
            task: Task entity to insert

        Returns:
            TaskModel ORM object that was added to the session

        Note:
            - The task is added to the session but not committed
            - Call session.flush() to get the generated ID immediately
            - Call session.commit() to persist the change
        """
        model = self._mapper.to_model(task)
        self._session.add(model)
        self._session.flush()  # Get ID immediately for downstream operations
        return model
