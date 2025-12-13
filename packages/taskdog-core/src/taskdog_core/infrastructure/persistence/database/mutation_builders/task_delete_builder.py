"""Builder for DELETE operations on Task entities.

This builder handles the deletion of task records from the database,
including hard delete operations with automatic CASCADE deletion of
related records.
"""

from sqlalchemy.orm import Session

from taskdog_core.infrastructure.persistence.database.models import TaskModel


class TaskDeleteBuilder:
    """Builder for deleting Task entities from the database.

    This builder handles DELETE operations, removing TaskModel ORM objects
    from the database. CASCADE rules automatically handle related records
    (e.g., task_tags junction table entries).

    Example:
        >>> builder = TaskDeleteBuilder(session)
        >>> deleted = builder.delete_task(task_id)
        >>> if deleted:
        ...     session.commit()  # Persist the deletion
    """

    def __init__(self, session: Session):
        """Initialize the builder.

        Args:
            session: SQLAlchemy session for database operations
        """
        self._session = session

    def delete_task(self, task_id: int) -> bool:
        """Hard delete a task by its ID.

        Args:
            task_id: ID of the task to delete

        Returns:
            True if the task was found and deleted, False otherwise

        Note:
            - Performs a hard delete (permanent removal)
            - CASCADE rules automatically delete related records:
              - task_tags junction table entries
            - Changes are tracked by SQLAlchemy session but not committed
            - Call session.commit() to persist the deletion
        """
        model = self._session.get(TaskModel, task_id)
        if model:
            self._session.delete(model)
            return True
        return False
