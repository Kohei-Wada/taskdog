"""Tests for RepositoryFactory."""

import tempfile
import unittest
from pathlib import Path

from taskdog_core.infrastructure.persistence.database.sqlite_task_repository import (
    SqliteTaskRepository,
)
from taskdog_core.infrastructure.persistence.repository_factory import RepositoryFactory
from taskdog_core.shared.server_config_manager import StorageConfig


class TestRepositoryFactory(unittest.TestCase):
    """Test suite for RepositoryFactory."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        """Clean up test files."""
        import shutil

        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_create_sqlite_repository(self) -> None:
        """Test factory creates SqliteTaskRepository for 'sqlite' backend."""
        db_path = Path(self.temp_dir) / "test.db"
        config = StorageConfig(backend="sqlite", database_url=f"sqlite:///{db_path}")

        repository = RepositoryFactory.create(config)

        self.assertIsInstance(repository, SqliteTaskRepository)
        # Clean up
        if hasattr(repository, "close"):
            repository.close()

    def test_create_sqlite_repository_with_default_url(self) -> None:
        """Test factory creates SqliteTaskRepository with default URL when None provided."""
        config = StorageConfig(backend="sqlite", database_url=None)

        repository = RepositoryFactory.create(config)

        self.assertIsInstance(repository, SqliteTaskRepository)
        # Verify it has a database_url set
        self.assertIsNotNone(repository.database_url)
        self.assertIn("sqlite:///", repository.database_url)
        # Clean up
        if hasattr(repository, "close"):
            repository.close()

    def test_create_with_uppercase_backend(self) -> None:
        """Test factory handles uppercase backend names."""
        db_path = Path(self.temp_dir) / "test.db"
        config = StorageConfig(backend="SQLITE", database_url=f"sqlite:///{db_path}")

        repository = RepositoryFactory.create(config)

        self.assertIsInstance(repository, SqliteTaskRepository)
        # Clean up
        if hasattr(repository, "close"):
            repository.close()

    def test_create_with_mixed_case_backend(self) -> None:
        """Test factory handles mixed case backend names."""
        config = StorageConfig(
            backend="SqLiTe", database_url=f"sqlite:///{self.temp_dir}/test.db"
        )

        repository = RepositoryFactory.create(config)

        self.assertIsInstance(repository, SqliteTaskRepository)
        # Clean up
        if hasattr(repository, "close"):
            repository.close()

    def test_create_with_unsupported_backend_raises_error(self) -> None:
        """Test factory raises ValueError for unsupported backend."""
        config = StorageConfig(backend="postgresql")

        with self.assertRaises(ValueError) as context:
            RepositoryFactory.create(config)

        self.assertIn("Unsupported storage backend", str(context.exception))
        self.assertIn("postgresql", str(context.exception))

    def test_sqlite_repository_is_functional(self) -> None:
        """Test created SQLite repository is functional."""
        db_path = Path(self.temp_dir) / "test.db"
        config = StorageConfig(backend="sqlite", database_url=f"sqlite:///{db_path}")

        repository = RepositoryFactory.create(config)

        try:
            # Test basic functionality
            task = repository.create("Test Task", priority=1)
            self.assertEqual(task.name, "Test Task")
            self.assertEqual(task.id, 1)

            # Verify persistence
            retrieved = repository.get_by_id(1)
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.name, "Test Task")
        finally:
            # Clean up
            if hasattr(repository, "close"):
                repository.close()


if __name__ == "__main__":
    unittest.main()
