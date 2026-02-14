"""Base class for query services."""

from taskdog_core.domain.repositories.task_repository import TaskRepository


class QueryService:
    """Base class for query services.

    Query services handle read-only operations and complex filtering logic.
    They are optimized for data retrieval and don't modify state.

    Attributes:
        repository: Task repository for data access

    Example:
        class TaskQueryService(QueryService):
            def __init__(self, repository):
                super().__init__(repository)

            def get_filtered_tasks(self, filter_obj=None):
                tasks = self.repository.get_all()
                return filter_obj.filter(tasks) if filter_obj else tasks
    """

    def __init__(self, repository: TaskRepository):
        """Initialize query service with repository.

        Args:
            repository: Task repository for data access
        """
        self.repository = repository
