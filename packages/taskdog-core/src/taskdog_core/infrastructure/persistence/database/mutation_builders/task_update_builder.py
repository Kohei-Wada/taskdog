"""Builder for UPDATE operations on Task entities.

This builder handles updates to existing task records in the database,
applying changes from Task entities to TaskModel ORM objects.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from taskdog_core.domain.entities.task import Task
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
            - Changes are tracked by SQLAlchemy session but not committed
            - Call session.commit() to persist the change
        """
        self._mapper.update_model(model, task)
        model.updated_at = datetime.now()

    def update_tasks_bulk(
        self, models: dict[int, TaskModel], tasks: list[Task]
    ) -> None:
        """Bulk update multiple tasks in a single operation.

        Args:
            models: Dictionary mapping task IDs to TaskModel ORM objects
            tasks: List of Task entities with updated data

        Note:
            - Only updates tasks that exist in the models dict
            - Skips tasks whose IDs are not in models
            - More efficient than calling update_task() individually
            - Call session.commit() to persist all changes at once
        """
        for task in tasks:
            if task.id in models:
                self.update_task(models[task.id], task)
