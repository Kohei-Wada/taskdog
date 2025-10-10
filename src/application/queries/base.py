"""Base class for query services."""

from infrastructure.persistence.task_repository import TaskRepository


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
                self.today_filter = TodayFilter(repository)

            def get_today_tasks(self, include_completed=False):
                tasks = self.repository.get_all()
                return self.today_filter.apply(tasks, include_completed)
    """

    def __init__(self, repository: TaskRepository):
        """Initialize query service with repository.

        Args:
            repository: Task repository for data access
        """
        self.repository = repository
