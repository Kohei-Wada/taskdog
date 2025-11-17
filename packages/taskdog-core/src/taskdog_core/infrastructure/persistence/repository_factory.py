"""Factory for creating TaskRepository instances based on configuration.

This factory provides a unified interface for creating SQLite repository
implementations based on storage backend configuration.
"""

from taskdog_core.domain.repositories.task_repository import TaskRepository
from taskdog_core.infrastructure.persistence.database.sqlite_task_repository import (
    SqliteTaskRepository,
)
from taskdog_core.infrastructure.persistence.mappers.task_db_mapper import TaskDbMapper
from taskdog_core.shared.server_config_manager import StorageConfig
from taskdog_core.shared.xdg_utils import XDGDirectories


class RepositoryFactory:
    """Factory for creating TaskRepository instances.

    This factory creates SQLite repository implementation based on
    the storage backend configuration.
    """

    @staticmethod
    def create(storage_config: StorageConfig) -> TaskRepository:
        """Create a TaskRepository instance based on storage configuration.

        Args:
            storage_config: Storage backend configuration

        Returns:
            TaskRepository instance (SqliteTaskRepository)

        Raises:
            ValueError: If backend is not supported
        """
        backend = storage_config.backend.lower()

        if backend == "sqlite":
            return RepositoryFactory._create_sqlite_repository(storage_config)
        else:
            raise ValueError(
                f"Unsupported storage backend: {storage_config.backend}. "
                f"Only 'sqlite' backend is supported."
            )

    @staticmethod
    def _create_sqlite_repository(
        storage_config: StorageConfig,
    ) -> SqliteTaskRepository:
        """Create a SQLite-based repository instance.

        Args:
            storage_config: Storage configuration with optional database_url

        Returns:
            SqliteTaskRepository with configured database URL
        """
        # Use custom database_url if provided, otherwise use default XDG location
        if storage_config.database_url:
            database_url = storage_config.database_url
        else:
            # Default: sqlite:///<XDG_DATA_HOME>/taskdog/tasks.db
            data_dir = XDGDirectories.get_data_home()
            db_file = data_dir / "tasks.db"
            database_url = f"sqlite:///{db_file}"

        mapper = TaskDbMapper()
        return SqliteTaskRepository(database_url, mapper)
