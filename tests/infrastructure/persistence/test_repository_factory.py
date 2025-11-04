"""Tests for RepositoryFactory."""

import tempfile
import unittest
from pathlib import Path

from infrastructure.persistence.database.sqlite_task_repository import SqliteTaskRepository
from infrastructure.persistence.json_task_repository import JsonTaskRepository
from infrastructure.persistence.repository_factory import RepositoryFactory
from shared.config_manager import StorageConfig


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

    def test_create_json_repository(self) -> None:
        """Test factory creates JsonTaskRepository for 'json' backend."""
        config = StorageConfig(backend="json")

        repository = RepositoryFactory.create(config)

        self.assertIsInstance(repository, JsonTaskRepository)

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
        config = StorageConfig(backend="JSON")

        repository = RepositoryFactory.create(config)

        self.assertIsInstance(repository, JsonTaskRepository)

    def test_create_with_mixed_case_backend(self) -> None:
        """Test factory handles mixed case backend names."""
        config = StorageConfig(backend="SqLiTe", database_url=f"sqlite:///{self.temp_dir}/test.db")

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

    def test_json_repository_is_functional(self) -> None:
        """Test created JSON repository is functional."""
        config = StorageConfig(backend="json")

        repository = RepositoryFactory.create(config)

        # Test basic functionality
        task = repository.create("Test Task", priority=1)
        self.assertEqual(task.name, "Test Task")
        # ID may not be 1 if tasks.json already exists, just verify it's set
        self.assertIsNotNone(task.id)
        self.assertGreater(task.id, 0)

        # Verify persistence
        retrieved = repository.get_by_id(task.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Test Task")

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

    def test_default_storage_config_creates_json_repository(self) -> None:
        """Test default StorageConfig creates JSON repository."""
        config = StorageConfig()  # Uses default backend="json"

        repository = RepositoryFactory.create(config)

        self.assertIsInstance(repository, JsonTaskRepository)


if __name__ == "__main__":
    unittest.main()
