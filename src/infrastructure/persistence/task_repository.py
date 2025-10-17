from abc import ABC, abstractmethod

from domain.entities.task import Task


class TaskRepository(ABC):
    """Abstract interface for task data persistence."""

    @abstractmethod
    def get_all(self) -> list[Task]:
        """Retrieve all tasks.

        Returns:
            List of all tasks
        """
        pass

    @abstractmethod
    def get_by_id(self, task_id: int) -> Task | None:
        """Retrieve a task by its ID.

        Args:
            task_id: The ID of the task to retrieve

        Returns:
            The task if found, None otherwise
        """
        pass

    @abstractmethod
    def save(self, task: Task) -> None:
        """Save a task (create new or update existing).

        Args:
            task: The task to save
        """
        pass

    @abstractmethod
    def delete(self, task_id: int) -> None:
        """Delete a task by its ID.

        Args:
            task_id: The ID of the task to delete
        """
        pass

    @abstractmethod
    def generate_next_id(self) -> int:
        """Generate the next available task ID.

        Returns:
            The next available ID
        """
        pass

    @abstractmethod
    def create(self, name: str, priority: int, **kwargs) -> Task:
        """Create a new task with auto-generated ID and save it.

        Args:
            name: Task name
            priority: Task priority
            **kwargs: Additional task fields

        Returns:
            Created task with ID assigned
        """
        pass

    @abstractmethod
    def reload(self) -> None:
        """Reload tasks from the data source.

        This method refreshes the in-memory cache from the underlying data source,
        allowing detection of changes made by external processes.
        """
        pass
