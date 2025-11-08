"""
Base test classes for taskdog-core tests.

This module provides common test infrastructure to reduce duplication across test files.
"""

import os
import tempfile
import unittest

from taskdog_core.infrastructure.persistence.database.sqlite_task_repository import (
    SqliteTaskRepository,
)


class BaseRepositoryTestCase(unittest.TestCase):
    """Base class for tests requiring SqliteTaskRepository.

    This class provides common setUp/tearDown for database tests, eliminating
    duplication across 26+ test files.

    Usage:
        class TestMyUseCase(BaseRepositoryTestCase):
            def setUp(self):
                super().setUp()
                self.use_case = MyUseCase(self.repository)

            def test_something(self):
                # self.repository is already available
                ...

    Attributes:
        test_file: Temporary file handle (for cleanup)
        test_filename: Path to temporary database file
        repository: SqliteTaskRepository instance connected to temporary database
    """

    def setUp(self):
        """Create temporary SQLite database and initialize repository.

        Creates a temporary .db file and initializes SqliteTaskRepository.
        The database is isolated per test method.
        """
        self.test_file = tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".db"
        )
        self.test_file.close()
        self.test_filename = self.test_file.name
        self.repository = SqliteTaskRepository(f"sqlite:///{self.test_filename}")

    def tearDown(self):
        """Clean up temporary database file.

        Closes repository connection and deletes temporary database file.
        Handles cases where repository or file may not exist.
        """
        if hasattr(self, "repository") and hasattr(self.repository, "close"):
            self.repository.close()
        if hasattr(self, "test_filename") and os.path.exists(self.test_filename):
            os.unlink(self.test_filename)
