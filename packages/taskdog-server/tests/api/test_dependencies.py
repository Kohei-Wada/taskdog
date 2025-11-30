"""Tests for FastAPI dependency injection."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi import FastAPI

from taskdog_server.api.context import ApiContext
from taskdog_server.api.dependencies import (
    get_analytics_controller,
    get_api_context,
    get_config,
    get_connection_manager,
    get_crud_controller,
    get_holiday_checker,
    get_lifecycle_controller,
    get_notes_repository,
    get_query_controller,
    get_relationship_controller,
    get_repository,
    initialize_api_context,
    reset_app_state,
    set_api_context,
)


class TestDependencyInjection(unittest.TestCase):
    """Test cases for dependency injection functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = FastAPI()

    def tearDown(self):
        """Clean up after tests."""
        reset_app_state(self.app)

    def _create_mock_request(self) -> MagicMock:
        """Create a mock request with app reference."""
        mock_request = MagicMock()
        mock_request.app = self.app
        return mock_request

    def test_set_and_get_api_context(self):
        """Test setting and getting API context via app.state."""
        # Arrange - create mock context
        mock_context = MagicMock(spec=ApiContext)

        # Act
        set_api_context(self.app, mock_context)
        mock_request = self._create_mock_request()
        retrieved_context = get_api_context(mock_request)

        # Assert
        self.assertEqual(retrieved_context, mock_context)

    def test_get_api_context_raises_when_not_initialized(self):
        """Test that get_api_context raises error when not initialized."""
        # Arrange
        mock_request = self._create_mock_request()

        # Act & Assert
        with self.assertRaises(RuntimeError) as context:
            get_api_context(mock_request)

        self.assertIn("not initialized", str(context.exception))

    def test_initialize_api_context_creates_all_dependencies(self):
        """Test that initialize_api_context creates all required dependencies."""
        # Arrange - create temporary config file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".toml") as f:
            config_path = f.name
            # Write minimal config
            f.write("[task]\ndefault_priority = 3\n")
            f.write("[scheduling]\nmax_hours_per_day = 8.0\n")
            f.write('default_algorithm = "greedy"\n')
            f.write('[storage]\nbackend = "sqlite"\n')
            f.write('database_url = "sqlite:///:memory:"\n')

        try:
            # Mock XDG config path to use our temp file
            with patch(
                "taskdog_core.shared.xdg_utils.XDGDirectories.get_config_file",
                return_value=Path(config_path),
            ):
                # Act
                context = initialize_api_context()

                # Assert
                self.assertIsNotNone(context)
                self.assertIsNotNone(context.repository)
                self.assertIsNotNone(context.config)
                self.assertIsNotNone(context.notes_repository)
                self.assertIsNotNone(context.query_controller)
                self.assertIsNotNone(context.lifecycle_controller)
                self.assertIsNotNone(context.relationship_controller)
                self.assertIsNotNone(context.analytics_controller)
                self.assertIsNotNone(context.crud_controller)
        finally:
            # Cleanup
            if os.path.exists(config_path):
                os.unlink(config_path)

    def test_get_query_controller(self):
        """Test getting query controller from context."""
        # Arrange
        mock_controller = MagicMock()
        mock_context = MagicMock(spec=ApiContext)
        mock_context.query_controller = mock_controller

        # Act
        controller = get_query_controller(mock_context)

        # Assert
        self.assertEqual(controller, mock_controller)

    def test_get_lifecycle_controller(self):
        """Test getting lifecycle controller from context."""
        # Arrange
        mock_controller = MagicMock()
        mock_context = MagicMock(spec=ApiContext)
        mock_context.lifecycle_controller = mock_controller

        # Act
        controller = get_lifecycle_controller(mock_context)

        # Assert
        self.assertEqual(controller, mock_controller)

    def test_get_relationship_controller(self):
        """Test getting relationship controller from context."""
        # Arrange
        mock_controller = MagicMock()
        mock_context = MagicMock(spec=ApiContext)
        mock_context.relationship_controller = mock_controller

        # Act
        controller = get_relationship_controller(mock_context)

        # Assert
        self.assertEqual(controller, mock_controller)

    def test_get_analytics_controller(self):
        """Test getting analytics controller from context."""
        # Arrange
        mock_controller = MagicMock()
        mock_context = MagicMock(spec=ApiContext)
        mock_context.analytics_controller = mock_controller

        # Act
        controller = get_analytics_controller(mock_context)

        # Assert
        self.assertEqual(controller, mock_controller)

    def test_get_crud_controller(self):
        """Test getting CRUD controller from context."""
        # Arrange
        mock_controller = MagicMock()
        mock_context = MagicMock(spec=ApiContext)
        mock_context.crud_controller = mock_controller

        # Act
        controller = get_crud_controller(mock_context)

        # Assert
        self.assertEqual(controller, mock_controller)

    def test_get_repository(self):
        """Test getting repository from context."""
        # Arrange
        mock_repository = MagicMock()
        mock_context = MagicMock(spec=ApiContext)
        mock_context.repository = mock_repository

        # Act
        repository = get_repository(mock_context)

        # Assert
        self.assertEqual(repository, mock_repository)

    def test_get_notes_repository(self):
        """Test getting notes repository from context."""
        # Arrange
        mock_notes_repo = MagicMock()
        mock_context = MagicMock(spec=ApiContext)
        mock_context.notes_repository = mock_notes_repo

        # Act
        notes_repo = get_notes_repository(mock_context)

        # Assert
        self.assertEqual(notes_repo, mock_notes_repo)

    def test_get_config(self):
        """Test getting config from context."""
        # Arrange
        mock_config = MagicMock()
        mock_context = MagicMock(spec=ApiContext)
        mock_context.config = mock_config

        # Act
        config = get_config(mock_context)

        # Assert
        self.assertEqual(config, mock_config)

    def test_get_holiday_checker_returns_none_when_not_configured(self):
        """Test getting holiday checker when not configured."""
        # Arrange
        mock_context = MagicMock(spec=ApiContext)
        mock_context.holiday_checker = None

        # Act
        checker = get_holiday_checker(mock_context)

        # Assert
        self.assertIsNone(checker)

    def test_get_holiday_checker_returns_instance_when_configured(self):
        """Test getting holiday checker when configured."""
        # Arrange
        mock_checker = MagicMock()
        mock_context = MagicMock(spec=ApiContext)
        mock_context.holiday_checker = mock_checker

        # Act
        checker = get_holiday_checker(mock_context)

        # Assert
        self.assertEqual(checker, mock_checker)

    def test_context_stored_in_app_state(self):
        """Test that context is stored in app.state."""
        # Arrange
        mock_context = MagicMock(spec=ApiContext)

        # Act
        set_api_context(self.app, mock_context)
        mock_request = self._create_mock_request()
        context1 = get_api_context(mock_request)
        context2 = get_api_context(mock_request)

        # Assert
        self.assertIs(context1, context2)
        self.assertIs(context1, mock_context)
        self.assertIs(self.app.state.api_context, mock_context)

    def test_setting_new_context_replaces_old(self):
        """Test that setting new context replaces the old one."""
        # Arrange
        mock_context1 = MagicMock(spec=ApiContext)
        mock_context2 = MagicMock(spec=ApiContext)
        mock_request = self._create_mock_request()

        # Act
        set_api_context(self.app, mock_context1)
        context1 = get_api_context(mock_request)

        set_api_context(self.app, mock_context2)
        context2 = get_api_context(mock_request)

        # Assert
        self.assertEqual(context1, mock_context1)
        self.assertEqual(context2, mock_context2)
        self.assertNotEqual(context1, context2)

    def test_get_connection_manager_lazy_init(self):
        """Test that connection manager is lazily initialized."""
        # Arrange
        mock_request = self._create_mock_request()

        # Act - first call should initialize
        manager1 = get_connection_manager(mock_request)
        manager2 = get_connection_manager(mock_request)

        # Assert
        self.assertIsNotNone(manager1)
        self.assertIs(manager1, manager2)
        self.assertIs(self.app.state.connection_manager, manager1)

    def test_reset_app_state(self):
        """Test that reset_app_state clears all state."""
        # Arrange
        mock_context = MagicMock(spec=ApiContext)
        set_api_context(self.app, mock_context)
        mock_request = self._create_mock_request()
        get_connection_manager(mock_request)  # Initialize connection manager

        # Act
        reset_app_state(self.app)

        # Assert
        self.assertFalse(hasattr(self.app.state, "api_context"))
        self.assertFalse(hasattr(self.app.state, "connection_manager"))


class TestInitializeApiContext(unittest.TestCase):
    """Test cases for initialize_api_context function."""

    def test_initialize_creates_all_controllers(self):
        """Test that initialization creates all required controllers."""
        # Arrange - create temporary config
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".toml") as f:
            config_path = f.name
            f.write("[task]\ndefault_priority = 3\n")
            f.write("[scheduling]\nmax_hours_per_day = 8.0\n")
            f.write('default_algorithm = "greedy"\n')
            f.write('[storage]\nbackend = "sqlite"\n')
            f.write('database_url = "sqlite:///:memory:"\n')

        try:
            with patch(
                "taskdog_core.shared.xdg_utils.XDGDirectories.get_config_file",
                return_value=Path(config_path),
            ):
                # Act
                context = initialize_api_context()

                # Assert - verify all controllers are created
                self.assertIsNotNone(context.query_controller)
                self.assertIsNotNone(context.lifecycle_controller)
                self.assertIsNotNone(context.relationship_controller)
                self.assertIsNotNone(context.analytics_controller)
                self.assertIsNotNone(context.crud_controller)
        finally:
            if os.path.exists(config_path):
                os.unlink(config_path)

    def test_initialize_creates_holiday_checker_when_country_configured(self):
        """Test that holiday checker is created when country is configured."""
        # Arrange - create config with country
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".toml") as f:
            config_path = f.name
            f.write("[task]\ndefault_priority = 3\n")
            f.write("[scheduling]\nmax_hours_per_day = 8.0\n")
            f.write('default_algorithm = "greedy"\n')
            f.write('[storage]\nbackend = "sqlite"\n')
            f.write('database_url = "sqlite:///:memory:"\n')
            f.write('[region]\ncountry = "US"\n')

        try:
            with patch(
                "taskdog_core.shared.xdg_utils.XDGDirectories.get_config_file",
                return_value=Path(config_path),
            ):
                # Act
                context = initialize_api_context()

                # Assert - holiday checker should be created
                self.assertIsNotNone(context.holiday_checker)
        finally:
            if os.path.exists(config_path):
                os.unlink(config_path)

    def test_initialize_handles_missing_holiday_library_gracefully(self):
        """Test that initialization continues even if holiday library is missing."""
        # Arrange - create config with country
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".toml") as f:
            config_path = f.name
            f.write("[task]\ndefault_priority = 3\n")
            f.write("[scheduling]\nmax_hours_per_day = 8.0\n")
            f.write('default_algorithm = "greedy"\n')
            f.write('[storage]\nbackend = "sqlite"\n')
            f.write('database_url = "sqlite:///:memory:"\n')
            f.write('[region]\ncountry = "XX"\n')  # Invalid country code

        try:
            with patch(
                "taskdog_core.shared.xdg_utils.XDGDirectories.get_config_file",
                return_value=Path(config_path),
            ):
                # Act - should not raise exception
                context = initialize_api_context()

                # Assert - context should be created even if holiday checker fails
                self.assertIsNotNone(context)
                # Holiday checker may be None if it failed to initialize
        finally:
            if os.path.exists(config_path):
                os.unlink(config_path)


if __name__ == "__main__":
    unittest.main()
