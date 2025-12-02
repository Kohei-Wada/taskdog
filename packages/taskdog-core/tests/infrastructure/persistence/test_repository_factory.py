"""Tests for RepositoryFactory."""

from pathlib import Path

import pytest

from taskdog_core.infrastructure.persistence.database.sqlite_task_repository import (
    SqliteTaskRepository,
)
from taskdog_core.infrastructure.persistence.repository_factory import RepositoryFactory
from taskdog_core.shared.config_manager import StorageConfig


class TestRepositoryFactory:
    """Test suite for RepositoryFactory."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up test fixtures."""
        self.temp_dir = tmp_path

    def test_create_sqlite_repository(self):
        """Test factory creates SqliteTaskRepository for 'sqlite' backend."""
        db_path = Path(self.temp_dir) / "test.db"
        config = StorageConfig(backend="sqlite", database_url=f"sqlite:///{db_path}")

        repository = RepositoryFactory.create(config)

        assert isinstance(repository, SqliteTaskRepository)
        # Clean up
        if hasattr(repository, "close"):
            repository.close()

    def test_create_sqlite_repository_with_default_url(self):
        """Test factory creates SqliteTaskRepository with default URL when None provided."""
        config = StorageConfig(backend="sqlite", database_url=None)

        repository = RepositoryFactory.create(config)

        assert isinstance(repository, SqliteTaskRepository)
        # Verify it has a database_url set
        assert repository.database_url is not None
        assert "sqlite:///" in repository.database_url
        # Clean up
        if hasattr(repository, "close"):
            repository.close()

    def test_create_with_uppercase_backend(self):
        """Test factory handles uppercase backend names."""
        db_path = Path(self.temp_dir) / "test.db"
        config = StorageConfig(backend="SQLITE", database_url=f"sqlite:///{db_path}")

        repository = RepositoryFactory.create(config)

        assert isinstance(repository, SqliteTaskRepository)
        # Clean up
        if hasattr(repository, "close"):
            repository.close()

    def test_create_with_mixed_case_backend(self):
        """Test factory handles mixed case backend names."""
        config = StorageConfig(
            backend="SqLiTe", database_url=f"sqlite:///{self.temp_dir}/test.db"
        )

        repository = RepositoryFactory.create(config)

        assert isinstance(repository, SqliteTaskRepository)
        # Clean up
        if hasattr(repository, "close"):
            repository.close()

    def test_create_with_unsupported_backend_raises_error(self):
        """Test factory raises ValueError for unsupported backend."""
        config = StorageConfig(backend="postgresql")

        with pytest.raises(ValueError) as exc_info:
            RepositoryFactory.create(config)

        assert "Unsupported storage backend" in str(exc_info.value)
        assert "postgresql" in str(exc_info.value)

    def test_sqlite_repository_is_functional(self):
        """Test created SQLite repository is functional."""
        db_path = Path(self.temp_dir) / "test.db"
        config = StorageConfig(backend="sqlite", database_url=f"sqlite:///{db_path}")

        repository = RepositoryFactory.create(config)

        try:
            # Test basic functionality
            task = repository.create("Test Task", priority=1)
            assert task.name == "Test Task"
            assert task.id == 1

            # Verify persistence
            retrieved = repository.get_by_id(1)
            assert retrieved is not None
            assert retrieved.name == "Test Task"
        finally:
            # Clean up
            if hasattr(repository, "close"):
                repository.close()
