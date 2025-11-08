"""
Base test classes for taskdog-server tests.

This module provides common test infrastructure for API router tests,
eliminating ~80 lines of setup duplication per test file.
"""

import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from taskdog_core.controllers.query_controller import QueryController
from taskdog_core.controllers.task_analytics_controller import TaskAnalyticsController
from taskdog_core.controllers.task_crud_controller import TaskCrudController
from taskdog_core.controllers.task_lifecycle_controller import TaskLifecycleController
from taskdog_core.controllers.task_relationship_controller import (
    TaskRelationshipController,
)
from taskdog_core.domain.entities.task import Task
from taskdog_core.infrastructure.persistence.database.sqlite_task_repository import (
    SqliteTaskRepository,
)
from taskdog_core.infrastructure.persistence.file_notes_repository import (
    FileNotesRepository,
)
from taskdog_server.api.context import ApiContext
from taskdog_server.api.dependencies import set_api_context


class BaseApiRouterTestCase(unittest.TestCase):
    """Base class for API router tests.

    This class provides common setUp/tearDown for API router tests, eliminating
    duplication across 3+ test files (~80 lines of setup each).

    Usage:
        class TestMyRouter(BaseApiRouterTestCase):
            def test_something(self):
                # self.client, self.repository, etc. are already available
                response = self.client.get("/api/v1/tasks")
                ...

    Attributes:
        test_db: Temporary database file handle
        test_db_path: Path to temporary database file
        test_notes_dir: Path to temporary notes directory
        repository: SqliteTaskRepository instance
        notes_repository: FileNotesRepository instance
        config: Mock config object with default settings
        client: FastAPI TestClient for making HTTP requests
        _next_task_id: Counter for generating sequential task IDs in tests
    """

    def setUp(self):
        """Set up test fixtures with real dependencies.

        Creates:
        - Temporary SQLite database
        - Temporary notes directory
        - All required controllers
        - FastAPI test client with all routers registered
        """
        # Create temporary database file
        self.test_db = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".db")
        self.test_db.close()
        self.test_db_path = self.test_db.name

        # Create temporary notes directory
        self.test_notes_dir = tempfile.mkdtemp()

        # Initialize repositories
        self.repository = SqliteTaskRepository(f"sqlite:///{self.test_db_path}")
        self.notes_repository = FileNotesRepository()

        # ID counter for test tasks
        self._next_task_id = 1

        # Mock config with defaults
        self.config = MagicMock()
        self.config.task.default_priority = 3
        self.config.scheduling.max_hours_per_day = 8.0
        self.config.scheduling.default_algorithm = "greedy"
        self.config.region.country = None

        # Create controllers
        query_controller = QueryController(self.repository, self.notes_repository)
        lifecycle_controller = TaskLifecycleController(self.repository, self.config)
        relationship_controller = TaskRelationshipController(
            self.repository, self.config
        )
        analytics_controller = TaskAnalyticsController(
            self.repository, self.config, None
        )
        crud_controller = TaskCrudController(self.repository, self.config)

        # Create API context
        api_context = ApiContext(
            repository=self.repository,
            config=self.config,
            notes_repository=self.notes_repository,
            query_controller=query_controller,
            lifecycle_controller=lifecycle_controller,
            relationship_controller=relationship_controller,
            analytics_controller=analytics_controller,
            crud_controller=crud_controller,
            holiday_checker=None,
        )

        # Set context BEFORE creating app
        set_api_context(api_context)

        # Create FastAPI app without lifespan to avoid reinitializing context
        app = FastAPI(
            title="Taskdog API Test",
            description="Test instance",
            version="1.0.0",
        )

        # Import and register routers
        from taskdog_server.api.routers import (
            analytics_router,
            lifecycle_router,
            notes_router,
            relationships_router,
            tasks_router,
        )

        app.include_router(tasks_router, prefix="/api/v1/tasks", tags=["tasks"])
        app.include_router(lifecycle_router, prefix="/api/v1/tasks", tags=["lifecycle"])
        app.include_router(
            relationships_router, prefix="/api/v1/tasks", tags=["relationships"]
        )
        app.include_router(notes_router, prefix="/api/v1/tasks", tags=["notes"])
        app.include_router(analytics_router, prefix="/api/v1", tags=["analytics"])

        # Create test client
        self.client = TestClient(app)

    def tearDown(self):
        """Clean up temporary files after each test.

        Closes database connection, removes temporary database file,
        and removes temporary notes directory.
        """
        if hasattr(self, "repository"):
            self.repository.close()
        if hasattr(self, "test_db_path") and os.path.exists(self.test_db_path):
            os.unlink(self.test_db_path)
        if hasattr(self, "test_notes_dir") and os.path.exists(self.test_notes_dir):
            shutil.rmtree(self.test_notes_dir)

    def _get_next_id(self):
        """Get next available task ID for tests.

        Returns:
            int: Sequential task ID starting from 1
        """
        task_id = self._next_task_id
        self._next_task_id += 1
        return task_id

    def create_task_in_db(self, **kwargs):
        """Helper to create a task directly in the database.

        Useful for setting up test data without going through the API.

        Args:
            **kwargs: Task attributes (name, priority, status, etc.)

        Returns:
            Task: The created task with ID assigned

        Example:
            task = self.create_task_in_db(
                name="Test Task",
                priority=2,
                status=TaskStatus.IN_PROGRESS
            )
        """
        task_id = self._get_next_id()
        task = Task(id=task_id, **kwargs)
        self.repository.save(task)
        return task
