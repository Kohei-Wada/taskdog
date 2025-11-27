"""Base test class for API router tests.

This module provides a shared base class for all server API router tests,
significantly improving test performance by reusing database and controller
fixtures across tests (~50% speedup).
"""

import unittest
from unittest.mock import MagicMock, Mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from taskdog_core.controllers.query_controller import QueryController
from taskdog_core.controllers.task_analytics_controller import TaskAnalyticsController
from taskdog_core.controllers.task_crud_controller import TaskCrudController
from taskdog_core.controllers.task_lifecycle_controller import TaskLifecycleController
from taskdog_core.controllers.task_relationship_controller import (
    TaskRelationshipController,
)
from taskdog_core.domain.services.logger import Logger
from taskdog_core.infrastructure.persistence.database.sqlite_task_repository import (
    SqliteTaskRepository,
)
from taskdog_core.infrastructure.persistence.file_notes_repository import (
    FileNotesRepository,
)
from taskdog_server.api.context import ApiContext
from taskdog_server.api.dependencies import set_api_context


class BaseApiRouterTest(unittest.TestCase):
    """Base test class for API router tests with shared fixtures.

    Uses class-level in-memory database and shared controllers/client
    for ~50% performance improvement over per-test setup.

    Subclasses automatically get:
    - self.repository: In-memory SQLite repository
    - self.notes_repository: File notes repository
    - self.client: FastAPI TestClient
    - self.config: Mock config object

    The database is cleared before each test, not recreated.
    """

    @classmethod
    def setUpClass(cls):
        """Set up shared test fixtures once for all tests."""
        if cls is BaseApiRouterTest:
            raise unittest.SkipTest("Skipping base test class")

        # In-memory database with shared cache (allows multiple connections to same DB)
        # The "file::memory:?cache=shared" syntax ensures all connections see the same data
        cls.repository = SqliteTaskRepository(
            "sqlite:///file::memory:?cache=shared&uri=true"
        )
        cls.notes_repository = FileNotesRepository()

        # Mock config with default values
        cls.config = MagicMock()
        cls.config.task.default_priority = 3
        cls.config.optimization.max_hours_per_day = 8.0
        cls.config.optimization.default_algorithm = "greedy"
        cls.config.region.country = None
        cls.config.time.default_start_hour = 9
        cls.config.time.default_end_hour = 18

        # Create mock logger for controllers
        cls.logger = Mock(spec=Logger)

        # Create controllers once (reused across all tests)
        query_controller = QueryController(
            cls.repository, cls.notes_repository, cls.logger
        )
        lifecycle_controller = TaskLifecycleController(
            cls.repository, cls.config, cls.logger
        )
        relationship_controller = TaskRelationshipController(
            cls.repository, cls.config, cls.logger
        )
        analytics_controller = TaskAnalyticsController(
            cls.repository, cls.config, None, cls.logger
        )
        crud_controller = TaskCrudController(
            cls.repository, cls.notes_repository, cls.config, cls.logger
        )

        # Create API context once
        api_context = ApiContext(
            repository=cls.repository,
            config=cls.config,
            notes_repository=cls.notes_repository,
            query_controller=query_controller,
            lifecycle_controller=lifecycle_controller,
            relationship_controller=relationship_controller,
            analytics_controller=analytics_controller,
            crud_controller=crud_controller,
            holiday_checker=None,
        )
        set_api_context(api_context)

        # Create FastAPI app once with all routers
        app = FastAPI(
            title="Taskdog API Test",
            description="Test instance",
            version="1.0.0",
        )

        # Import and register all routers
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

        # Create test client once (reused across all tests)
        cls.client = TestClient(app)

        # Initialize task ID counter
        cls._next_task_id = 1

    def setUp(self):
        """Clear database before each test."""
        # Clear all tasks - much faster than recreating database
        for task in self.repository.get_all():
            self.repository.delete(task.id)
        # Reset task ID counter
        self._next_task_id = 1

    def _get_next_id(self):
        """Get next available task ID for tests."""
        task_id = self._next_task_id
        self._next_task_id += 1
        return task_id

    @classmethod
    def tearDownClass(cls):
        """Clean up shared resources after all tests."""
        if hasattr(cls, "repository"):
            cls.repository.close()
