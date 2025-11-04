"""Factory for creating TaskRepository instances based on configuration.

This factory provides a unified interface for creating different repository
implementations (JSON, SQLite) based on storage backend configuration.
"""

from domain.repositories.task_repository import TaskRepository
from infrastructure.persistence.database.sqlite_task_repository import SqliteTaskRepository
from infrastructure.persistence.json_task_repository import JsonTaskRepository
from infrastructure.persistence.mappers.task_db_mapper import TaskDbMapper
from infrastructure.persistence.mappers.task_json_mapper import TaskJsonMapper
from shared.config_manager import StorageConfig
from shared.xdg_utils import XDGDirectories


class RepositoryFactory:
    """Factory for creating TaskRepository instances.

    This factory creates the appropriate repository implementation based on
    the storage backend configuration. Supports JSON and SQLite backends.
    """

    @staticmethod
    def create(storage_config: StorageConfig) -> TaskRepository:
        """Create a TaskRepository instance based on storage configuration.

        Args:
            storage_config: Storage backend configuration

        Returns:
            TaskRepository instance (JsonTaskRepository or SqliteTaskRepository)

        Raises:
            ValueError: If backend is not supported
        """
        backend = storage_config.backend.lower()

        if backend == "json":
            return RepositoryFactory._create_json_repository()
        elif backend == "sqlite":
            return RepositoryFactory._create_sqlite_repository(storage_config)
        else:
            raise ValueError(
                f"Unsupported storage backend: {storage_config.backend}. "
                f"Supported backends: json, sqlite"
            )

    @staticmethod
    def _create_json_repository() -> JsonTaskRepository:
        """Create a JSON-based repository instance.

        Returns:
            JsonTaskRepository with default JSON file path
        """
        tasks_file = str(XDGDirectories.get_tasks_file())
        mapper = TaskJsonMapper()
        return JsonTaskRepository(tasks_file, mapper)

    @staticmethod
    def _create_sqlite_repository(storage_config: StorageConfig) -> SqliteTaskRepository:
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
