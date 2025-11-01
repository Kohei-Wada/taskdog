"""Base controller with shared dependencies for all task controllers.

This module provides a base class that all specialized task controllers inherit from,
providing access to common dependencies like repository and config.
"""

from domain.repositories.task_repository import TaskRepository
from shared.config_manager import Config


class BaseTaskController:
    """Base class for all task controllers.

    Provides shared dependencies used across multiple controllers:
    - TaskRepository: For all data access operations
    - Config: For application configuration (priorities, algorithms, etc.)

    Specialized controllers inherit from this class and add their own
    specific dependencies (e.g., TimeTracker, NotesRepository).
    """

    def __init__(self, repository: TaskRepository, config: Config):
        """Initialize base controller with shared dependencies.

        Args:
            repository: Task repository for data access
            config: Application configuration
        """
        self.repository = repository
        self.config = config
