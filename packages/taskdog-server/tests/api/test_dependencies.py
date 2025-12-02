"""Tests for FastAPI dependency injection."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
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


class TestDependencyInjection:
    """Test cases for dependency injection functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = FastAPI()

    def teardown_method(self):
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
        assert retrieved_context == mock_context

    def test_get_api_context_raises_when_not_initialized(self):
        """Test that get_api_context raises error when not initialized."""
        # Arrange
        mock_request = self._create_mock_request()

        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            get_api_context(mock_request)

        assert "not initialized" in str(exc_info.value)

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
                assert context is not None
                assert context.repository is not None
                assert context.config is not None
                assert context.notes_repository is not None
                assert context.query_controller is not None
                assert context.lifecycle_controller is not None
                assert context.relationship_controller is not None
                assert context.analytics_controller is not None
                assert context.crud_controller is not None
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
        assert controller == mock_controller

    def test_get_lifecycle_controller(self):
        """Test getting lifecycle controller from context."""
        # Arrange
        mock_controller = MagicMock()
        mock_context = MagicMock(spec=ApiContext)
        mock_context.lifecycle_controller = mock_controller

        # Act
        controller = get_lifecycle_controller(mock_context)

        # Assert
        assert controller == mock_controller

    def test_get_relationship_controller(self):
        """Test getting relationship controller from context."""
        # Arrange
        mock_controller = MagicMock()
        mock_context = MagicMock(spec=ApiContext)
        mock_context.relationship_controller = mock_controller

        # Act
        controller = get_relationship_controller(mock_context)

        # Assert
        assert controller == mock_controller

    def test_get_analytics_controller(self):
        """Test getting analytics controller from context."""
        # Arrange
        mock_controller = MagicMock()
        mock_context = MagicMock(spec=ApiContext)
        mock_context.analytics_controller = mock_controller

        # Act
        controller = get_analytics_controller(mock_context)

        # Assert
        assert controller == mock_controller

    def test_get_crud_controller(self):
        """Test getting CRUD controller from context."""
        # Arrange
        mock_controller = MagicMock()
        mock_context = MagicMock(spec=ApiContext)
        mock_context.crud_controller = mock_controller

        # Act
        controller = get_crud_controller(mock_context)

        # Assert
        assert controller == mock_controller

    def test_get_repository(self):
        """Test getting repository from context."""
        # Arrange
        mock_repository = MagicMock()
        mock_context = MagicMock(spec=ApiContext)
        mock_context.repository = mock_repository

        # Act
        repository = get_repository(mock_context)

        # Assert
        assert repository == mock_repository

    def test_get_notes_repository(self):
        """Test getting notes repository from context."""
        # Arrange
        mock_notes_repo = MagicMock()
        mock_context = MagicMock(spec=ApiContext)
        mock_context.notes_repository = mock_notes_repo

        # Act
        notes_repo = get_notes_repository(mock_context)

        # Assert
        assert notes_repo == mock_notes_repo

    def test_get_config(self):
        """Test getting config from context."""
        # Arrange
        mock_config = MagicMock()
        mock_context = MagicMock(spec=ApiContext)
        mock_context.config = mock_config

        # Act
        config = get_config(mock_context)

        # Assert
        assert config == mock_config

    def test_get_holiday_checker_returns_none_when_not_configured(self):
        """Test getting holiday checker when not configured."""
        # Arrange
        mock_context = MagicMock(spec=ApiContext)
        mock_context.holiday_checker = None

        # Act
        checker = get_holiday_checker(mock_context)

        # Assert
        assert checker is None

    def test_get_holiday_checker_returns_instance_when_configured(self):
        """Test getting holiday checker when configured."""
        # Arrange
        mock_checker = MagicMock()
        mock_context = MagicMock(spec=ApiContext)
        mock_context.holiday_checker = mock_checker

        # Act
        checker = get_holiday_checker(mock_context)

        # Assert
        assert checker == mock_checker

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
        assert context1 is context2
        assert context1 is mock_context
        assert self.app.state.api_context is mock_context

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
        assert context1 == mock_context1
        assert context2 == mock_context2
        assert context1 != context2

    def test_get_connection_manager_lazy_init(self):
        """Test that connection manager is lazily initialized."""
        # Arrange
        mock_request = self._create_mock_request()

        # Act - first call should initialize
        manager1 = get_connection_manager(mock_request)
        manager2 = get_connection_manager(mock_request)

        # Assert
        assert manager1 is not None
        assert manager1 is manager2
        assert self.app.state.connection_manager is manager1

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
        assert not hasattr(self.app.state, "api_context")
        assert not hasattr(self.app.state, "connection_manager")


class TestInitializeApiContext:
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
                assert context.query_controller is not None
                assert context.lifecycle_controller is not None
                assert context.relationship_controller is not None
                assert context.analytics_controller is not None
                assert context.crud_controller is not None
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
                assert context.holiday_checker is not None
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
                assert context is not None
                # Holiday checker may be None if it failed to initialize
        finally:
            if os.path.exists(config_path):
                os.unlink(config_path)
