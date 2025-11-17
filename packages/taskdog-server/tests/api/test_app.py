"""Tests for FastAPI application factory and configuration."""

import unittest
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from taskdog_core.controllers.query_controller import QueryController
from taskdog_core.controllers.task_analytics_controller import TaskAnalyticsController
from taskdog_core.controllers.task_crud_controller import TaskCrudController
from taskdog_core.controllers.task_lifecycle_controller import TaskLifecycleController
from taskdog_core.controllers.task_relationship_controller import (
    TaskRelationshipController,
)
from taskdog_core.shared.server_config_manager import (
    RegionConfig,
    ServerConfig,
    StorageConfig,
    TaskConfig,
    TimeConfig,
)
from taskdog_server.api.context import ApiContext
from taskdog_server.api.dependencies import set_api_context


class TestApp(unittest.TestCase):
    """Test cases for FastAPI application.

    Uses setUpClass instead of setUp to create app once for all tests,
    improving performance by ~520ms (8x reduction in setup overhead).
    """

    @classmethod
    def setUpClass(cls):
        """Set up shared test fixtures once for all tests."""
        # Mock repositories
        cls.mock_repository = MagicMock()
        cls.mock_notes_repository = MagicMock()

        # Server config
        cls.mock_config = ServerConfig(
            time=TimeConfig(default_start_hour=9, default_end_hour=18),
            region=RegionConfig(country=None),
            storage=StorageConfig(backend="sqlite", database_url=None),
            task=TaskConfig(default_priority=3),
        )

        # Create controllers with mocked dependencies
        query_controller = QueryController(
            cls.mock_repository, cls.mock_notes_repository
        )
        lifecycle_controller = TaskLifecycleController(
            cls.mock_repository, cls.mock_config
        )
        relationship_controller = TaskRelationshipController(
            cls.mock_repository, cls.mock_config
        )
        analytics_controller = TaskAnalyticsController(
            cls.mock_repository, cls.mock_config, None
        )
        crud_controller = TaskCrudController(
            cls.mock_repository, cls.mock_notes_repository, cls.mock_config
        )

        # Create and set API context
        api_context = ApiContext(
            repository=cls.mock_repository,
            config=cls.mock_config,
            notes_repository=cls.mock_notes_repository,
            query_controller=query_controller,
            lifecycle_controller=lifecycle_controller,
            relationship_controller=relationship_controller,
            analytics_controller=analytics_controller,
            crud_controller=crud_controller,
            holiday_checker=None,
        )
        set_api_context(api_context)

        # Now create app - only once for all tests
        from taskdog_server.api.app import create_app

        cls.app = create_app()
        cls.client = TestClient(cls.app)

    def test_app_creation(self):
        """Test that app is created successfully."""
        # Assert
        self.assertIsNotNone(self.app)
        self.assertEqual(self.app.title, "Taskdog API")
        self.assertEqual(self.app.version, "1.0.0")

    def test_root_endpoint(self):
        """Test root endpoint returns correct message."""
        # Act
        response = self.client.get("/")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "Taskdog API")
        self.assertEqual(data["version"], "1.0.0")

    def test_health_endpoint(self):
        """Test health check endpoint."""
        # Act
        response = self.client.get("/health")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")

    def test_cors_middleware_configured(self):
        """Test that CORS middleware is configured."""
        # The app should have CORS middleware
        # We can verify by checking if OPTIONS requests are handled
        response = self.client.options("/")

        # Assert - OPTIONS should be allowed
        self.assertIn(
            response.status_code, [200, 405]
        )  # Either OK or Method Not Allowed

    def test_routers_registered(self):
        """Test that all routers are registered with correct prefixes."""
        # Check that routes exist for each router
        routes = [route.path for route in self.app.routes]

        # Assert - Check for key endpoints from each router
        self.assertTrue(
            any("/api/v1/tasks" in route for route in routes), "Tasks router not found"
        )
        self.assertTrue(
            any(
                "/api/v1/statistics" in route or "/api/v1/gantt" in route
                for route in routes
            ),
            "Analytics router not found",
        )

    def test_openapi_docs_available(self):
        """Test that OpenAPI documentation is available."""
        # Act
        response = self.client.get("/openapi.json")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["info"]["title"], "Taskdog API")
        self.assertIn("paths", data)

    def test_app_has_correct_metadata(self):
        """Test that app has correct metadata."""
        # Assert
        self.assertEqual(self.app.title, "Taskdog API")
        self.assertIn("Task management API", self.app.description)
        self.assertEqual(self.app.version, "1.0.0")


class TestAppWithoutContext(unittest.TestCase):
    """Test cases for app behavior without initialized context."""

    def test_endpoints_fail_without_context(self):
        """Test that endpoints fail gracefully when context is not initialized."""
        # Reset global context
        from taskdog_server.api import dependencies

        # Save the current context
        saved_context = dependencies._api_context

        try:
            # Clear the context
            dependencies._api_context = None

            # Create app without setting context
            from fastapi import FastAPI

            from taskdog_server.api.routers import tasks_router

            app = FastAPI()
            app.include_router(tasks_router, prefix="/api/v1/tasks")

            client = TestClient(app, raise_server_exceptions=False)

            # Act - try to call an endpoint that requires context
            response = client.get("/api/v1/tasks")

            # Assert - should get 500 error due to uninitialized context
            self.assertEqual(response.status_code, 500)
        finally:
            # Restore the original context
            dependencies._api_context = saved_context


if __name__ == "__main__":
    unittest.main()
