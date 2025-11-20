"""Tests for API context dataclass."""

import unittest
from unittest.mock import Mock

from taskdog_core.controllers.query_controller import QueryController
from taskdog_core.controllers.task_analytics_controller import TaskAnalyticsController
from taskdog_core.controllers.task_crud_controller import TaskCrudController
from taskdog_core.controllers.task_lifecycle_controller import TaskLifecycleController
from taskdog_core.controllers.task_relationship_controller import (
    TaskRelationshipController,
)
from taskdog_core.domain.repositories.notes_repository import NotesRepository
from taskdog_core.domain.repositories.task_repository import TaskRepository
from taskdog_core.domain.services.holiday_checker import IHolidayChecker
from taskdog_core.shared.config_manager import Config
from taskdog_server.api.context import ApiContext


class TestApiContext(unittest.TestCase):
    """Test cases for ApiContext dataclass."""

    def setUp(self):
        """Set up mock dependencies for tests."""
        self.mock_repository = Mock(spec=TaskRepository)
        self.mock_config = Mock(spec=Config)
        self.mock_notes_repository = Mock(spec=NotesRepository)
        self.mock_query_controller = Mock(spec=QueryController)
        self.mock_lifecycle_controller = Mock(spec=TaskLifecycleController)
        self.mock_relationship_controller = Mock(spec=TaskRelationshipController)
        self.mock_analytics_controller = Mock(spec=TaskAnalyticsController)
        self.mock_crud_controller = Mock(spec=TaskCrudController)
        self.mock_holiday_checker = Mock(spec=IHolidayChecker)

    def test_create_context_with_all_dependencies(self):
        """Test creating ApiContext with all dependencies."""
        # Act
        context = ApiContext(
            repository=self.mock_repository,
            config=self.mock_config,
            notes_repository=self.mock_notes_repository,
            query_controller=self.mock_query_controller,
            lifecycle_controller=self.mock_lifecycle_controller,
            relationship_controller=self.mock_relationship_controller,
            analytics_controller=self.mock_analytics_controller,
            crud_controller=self.mock_crud_controller,
            holiday_checker=self.mock_holiday_checker,
        )

        # Assert
        self.assertEqual(context.repository, self.mock_repository)
        self.assertEqual(context.config, self.mock_config)
        self.assertEqual(context.notes_repository, self.mock_notes_repository)
        self.assertEqual(context.query_controller, self.mock_query_controller)
        self.assertEqual(context.lifecycle_controller, self.mock_lifecycle_controller)
        self.assertEqual(
            context.relationship_controller, self.mock_relationship_controller
        )
        self.assertEqual(context.analytics_controller, self.mock_analytics_controller)
        self.assertEqual(context.crud_controller, self.mock_crud_controller)
        self.assertEqual(context.holiday_checker, self.mock_holiday_checker)

    def test_create_context_without_holiday_checker(self):
        """Test creating ApiContext without holiday checker (None)."""
        # Act
        context = ApiContext(
            repository=self.mock_repository,
            config=self.mock_config,
            notes_repository=self.mock_notes_repository,
            query_controller=self.mock_query_controller,
            lifecycle_controller=self.mock_lifecycle_controller,
            relationship_controller=self.mock_relationship_controller,
            analytics_controller=self.mock_analytics_controller,
            crud_controller=self.mock_crud_controller,
            holiday_checker=None,
        )

        # Assert
        self.assertIsNone(context.holiday_checker)

    def test_context_is_immutable_dataclass(self):
        """Test that ApiContext attributes can be accessed and modified."""
        # Act
        context = ApiContext(
            repository=self.mock_repository,
            config=self.mock_config,
            notes_repository=self.mock_notes_repository,
            query_controller=self.mock_query_controller,
            lifecycle_controller=self.mock_lifecycle_controller,
            relationship_controller=self.mock_relationship_controller,
            analytics_controller=self.mock_analytics_controller,
            crud_controller=self.mock_crud_controller,
            holiday_checker=self.mock_holiday_checker,
        )

        # Assert - verify all attributes are accessible
        self.assertIsNotNone(context.repository)
        self.assertIsNotNone(context.config)
        self.assertIsNotNone(context.notes_repository)
        self.assertIsNotNone(context.query_controller)
        self.assertIsNotNone(context.lifecycle_controller)
        self.assertIsNotNone(context.relationship_controller)
        self.assertIsNotNone(context.analytics_controller)
        self.assertIsNotNone(context.crud_controller)
        self.assertIsNotNone(context.holiday_checker)

    def test_context_with_different_repository_instances(self):
        """Test creating contexts with different repository instances."""
        # Arrange
        mock_repository2 = Mock(spec=TaskRepository)

        # Act
        context1 = ApiContext(
            repository=self.mock_repository,
            config=self.mock_config,
            notes_repository=self.mock_notes_repository,
            query_controller=self.mock_query_controller,
            lifecycle_controller=self.mock_lifecycle_controller,
            relationship_controller=self.mock_relationship_controller,
            analytics_controller=self.mock_analytics_controller,
            crud_controller=self.mock_crud_controller,
            holiday_checker=None,
        )

        context2 = ApiContext(
            repository=mock_repository2,
            config=self.mock_config,
            notes_repository=self.mock_notes_repository,
            query_controller=self.mock_query_controller,
            lifecycle_controller=self.mock_lifecycle_controller,
            relationship_controller=self.mock_relationship_controller,
            analytics_controller=self.mock_analytics_controller,
            crud_controller=self.mock_crud_controller,
            holiday_checker=None,
        )

        # Assert
        self.assertNotEqual(context1.repository, context2.repository)

    def test_context_with_different_controller_instances(self):
        """Test creating contexts with different controller instances."""
        # Arrange
        mock_query_controller2 = Mock(spec=QueryController)

        # Act
        context1 = ApiContext(
            repository=self.mock_repository,
            config=self.mock_config,
            notes_repository=self.mock_notes_repository,
            query_controller=self.mock_query_controller,
            lifecycle_controller=self.mock_lifecycle_controller,
            relationship_controller=self.mock_relationship_controller,
            analytics_controller=self.mock_analytics_controller,
            crud_controller=self.mock_crud_controller,
            holiday_checker=None,
        )

        context2 = ApiContext(
            repository=self.mock_repository,
            config=self.mock_config,
            notes_repository=self.mock_notes_repository,
            query_controller=mock_query_controller2,
            lifecycle_controller=self.mock_lifecycle_controller,
            relationship_controller=self.mock_relationship_controller,
            analytics_controller=self.mock_analytics_controller,
            crud_controller=self.mock_crud_controller,
            holiday_checker=None,
        )

        # Assert
        self.assertNotEqual(context1.query_controller, context2.query_controller)

    def test_context_stores_all_five_controllers(self):
        """Test that context stores all five specialized controllers."""
        # Act
        context = ApiContext(
            repository=self.mock_repository,
            config=self.mock_config,
            notes_repository=self.mock_notes_repository,
            query_controller=self.mock_query_controller,
            lifecycle_controller=self.mock_lifecycle_controller,
            relationship_controller=self.mock_relationship_controller,
            analytics_controller=self.mock_analytics_controller,
            crud_controller=self.mock_crud_controller,
            holiday_checker=None,
        )

        # Assert - verify all five controllers are present
        controllers = [
            context.query_controller,
            context.lifecycle_controller,
            context.relationship_controller,
            context.analytics_controller,
            context.crud_controller,
        ]

        # All controllers should be non-None
        for controller in controllers:
            self.assertIsNotNone(controller)

        # All controllers should be different instances
        self.assertEqual(len(set(map(id, controllers))), 5)


if __name__ == "__main__":
    unittest.main()
