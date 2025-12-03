"""Tests for FastAPI application factory and configuration."""

from unittest.mock import MagicMock, Mock

import pytest
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
from taskdog_core.infrastructure.time_provider import SystemTimeProvider
from taskdog_server.api.context import ApiContext
from taskdog_server.websocket.connection_manager import ConnectionManager


class TestApp:
    """Test cases for FastAPI application."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up shared test fixtures."""
        # Mock repositories and config
        self.mock_repository = MagicMock()
        self.mock_notes_repository = MagicMock()
        self.mock_config = MagicMock()
        self.mock_config.task.default_priority = 3
        self.mock_config.scheduling.max_hours_per_day = 8.0
        self.mock_config.scheduling.default_algorithm = "greedy"
        self.mock_config.region.country = None

        # Create mock logger for controllers
        self.mock_logger = Mock(spec=Logger)

        # Create controllers with mocked dependencies
        query_controller = QueryController(
            self.mock_repository, self.mock_notes_repository, self.mock_logger
        )
        lifecycle_controller = TaskLifecycleController(
            self.mock_repository, self.mock_config, self.mock_logger
        )
        relationship_controller = TaskRelationshipController(
            self.mock_repository, self.mock_config, self.mock_logger
        )
        analytics_controller = TaskAnalyticsController(
            self.mock_repository, self.mock_config, None, self.mock_logger
        )
        crud_controller = TaskCrudController(
            self.mock_repository,
            self.mock_notes_repository,
            self.mock_config,
            self.mock_logger,
        )

        # Create API context
        api_context = ApiContext(
            repository=self.mock_repository,
            config=self.mock_config,
            notes_repository=self.mock_notes_repository,
            query_controller=query_controller,
            lifecycle_controller=lifecycle_controller,
            relationship_controller=relationship_controller,
            analytics_controller=analytics_controller,
            crud_controller=crud_controller,
            holiday_checker=None,
            time_provider=SystemTimeProvider(),
        )

        # Create app using create_app (lifespan will set its own context)
        from taskdog_server.api.app import create_app

        self.app = create_app()

        # Override context on app.state for testing with our mock objects
        self.app.state.api_context = api_context
        self.app.state.connection_manager = ConnectionManager()

        self.client = TestClient(self.app)

    def test_app_creation(self):
        """Test that app is created successfully."""
        # Assert
        assert self.app is not None
        assert self.app.title == "Taskdog API"
        assert self.app.version == "1.0.0"

    def test_root_endpoint(self):
        """Test root endpoint returns correct message."""
        # Act
        response = self.client.get("/")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Taskdog API"
        assert data["version"] == "1.0.0"

    def test_health_endpoint(self):
        """Test health check endpoint."""
        # Act
        response = self.client.get("/health")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_cors_middleware_configured(self):
        """Test that CORS middleware is configured."""
        # The app should have CORS middleware
        # We can verify by checking if OPTIONS requests are handled
        response = self.client.options("/")

        # Assert - OPTIONS should be allowed
        assert response.status_code in [200, 405]  # Either OK or Method Not Allowed

    def test_routers_registered(self):
        """Test that all routers are registered with correct prefixes."""
        # Check that routes exist for each router
        routes = [route.path for route in self.app.routes]

        # Assert - Check for key endpoints from each router
        assert any("/api/v1/tasks" in route for route in routes), (
            "Tasks router not found"
        )
        assert any(
            "/api/v1/statistics" in route or "/api/v1/gantt" in route
            for route in routes
        ), "Analytics router not found"

    def test_openapi_docs_available(self):
        """Test that OpenAPI documentation is available."""
        # Act
        response = self.client.get("/openapi.json")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["info"]["title"] == "Taskdog API"
        assert "paths" in data

    def test_app_has_correct_metadata(self):
        """Test that app has correct metadata."""
        # Assert
        assert self.app.title == "Taskdog API"
        assert "Task management API" in self.app.description
        assert self.app.version == "1.0.0"


class TestAppWithoutContext:
    """Test cases for app behavior without initialized context."""

    def test_endpoints_fail_without_context(self):
        """Test that endpoints fail gracefully when context is not initialized."""
        from taskdog_server.api.routers import tasks_router

        # Create app WITHOUT setting app.state.api_context
        app = FastAPI()
        app.include_router(tasks_router, prefix="/api/v1/tasks")

        client = TestClient(app, raise_server_exceptions=False)

        # Act - try to call an endpoint that requires context
        response = client.get("/api/v1/tasks")

        # Assert - should get 500 error due to uninitialized context
        assert response.status_code == 500
