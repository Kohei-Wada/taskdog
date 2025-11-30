"""Tests for concurrent database access (Issue #226).

This module tests that the repository handles concurrent writes correctly
using SQLite AUTOINCREMENT for ID assignment.
"""

import shutil
import tempfile
import threading
import unittest
from pathlib import Path

from taskdog_core.infrastructure.persistence.database.sqlite_task_repository import (
    SqliteTaskRepository,
)


class TestConcurrentWrites(unittest.TestCase):
    """Test suite for concurrent database writes."""

    def setUp(self) -> None:
        """Set up test fixtures with temporary file database."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "concurrent_test.db"
        self.database_url = f"sqlite:///{self.db_path}"

    def tearDown(self) -> None:
        """Clean up database files."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_concurrent_task_creation_no_id_collision(self) -> None:
        """Test that concurrent task creation doesn't cause ID collisions."""
        num_threads = 10
        tasks_per_thread = 10
        created_ids: list[int] = []
        errors: list[Exception] = []
        lock = threading.Lock()

        # Create tables first with a single repository instance
        init_repo = SqliteTaskRepository(self.database_url)
        init_repo.close()

        def create_tasks() -> None:
            repo = SqliteTaskRepository(self.database_url)
            try:
                for i in range(tasks_per_thread):
                    task = repo.create(
                        name=f"Task from {threading.current_thread().name} #{i}",
                        priority=1,
                    )
                    with lock:
                        created_ids.append(task.id)  # type: ignore[arg-type]
            except Exception as e:
                with lock:
                    errors.append(e)
            finally:
                repo.close()

        threads = [
            threading.Thread(target=create_tasks, name=f"Thread-{i}")
            for i in range(num_threads)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify no errors
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")

        # Verify correct number of tasks created
        expected_count = num_threads * tasks_per_thread
        self.assertEqual(len(created_ids), expected_count)

        # Verify all IDs are unique (no duplicates)
        unique_ids = set(created_ids)
        self.assertEqual(
            len(unique_ids),
            len(created_ids),
            f"Duplicate IDs found! Created: {len(created_ids)}, Unique: {len(unique_ids)}",
        )

    def test_concurrent_writes_from_multiple_repository_instances(self) -> None:
        """Test concurrent writes from separate repository instances.

        This simulates the real-world scenario where CLI and API server
        both write to the same database file.
        """
        num_repos = 5
        writes_per_repo = 20
        results: list[int] = []
        errors: list[Exception] = []
        lock = threading.Lock()

        # Create tables first with a single repository instance
        init_repo = SqliteTaskRepository(self.database_url)
        init_repo.close()

        def write_tasks(repo_id: int) -> None:
            repo = SqliteTaskRepository(self.database_url)
            try:
                for i in range(writes_per_repo):
                    task = repo.create(
                        name=f"Task {i} from repo {repo_id}",
                        priority=1,
                    )
                    with lock:
                        results.append(task.id)  # type: ignore[arg-type]
            except Exception as e:
                with lock:
                    errors.append(e)
            finally:
                repo.close()

        threads = [
            threading.Thread(target=write_tasks, args=(i,)) for i in range(num_repos)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify no errors
        self.assertEqual(len(errors), 0, f"Errors: {errors}")

        # Verify correct count and uniqueness
        expected_count = num_repos * writes_per_repo
        self.assertEqual(len(results), expected_count)
        self.assertEqual(len(set(results)), len(results))

    def test_ids_are_sequential(self) -> None:
        """Test that IDs assigned by AUTOINCREMENT are sequential."""
        repo = SqliteTaskRepository(self.database_url)
        try:
            ids = []
            for i in range(10):
                task = repo.create(name=f"Task {i}", priority=1)
                ids.append(task.id)

            # IDs should be sequential starting from 1
            self.assertEqual(ids, list(range(1, 11)))
        finally:
            repo.close()


if __name__ == "__main__":
    unittest.main()
