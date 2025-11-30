"""FastAPI dependency injection functions."""

from contextlib import suppress
from typing import Annotated

from fastapi import BackgroundTasks, Depends

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
from taskdog_core.infrastructure.holiday_checker import HolidayChecker
from taskdog_core.infrastructure.persistence.file_notes_repository import (
    FileNotesRepository,
)
from taskdog_core.infrastructure.persistence.repository_factory import RepositoryFactory
from taskdog_core.shared.config_manager import Config, ConfigManager
from taskdog_server.api.context import ApiContext
from taskdog_server.infrastructure.logging.standard_logger import StandardLogger
from taskdog_server.websocket.broadcast_helper import BroadcastHelper
from taskdog_server.websocket.connection_manager import ConnectionManager

# Global context instance
_api_context: ApiContext | None = None

# Global connection manager instance
_connection_manager: ConnectionManager | None = None


def initialize_api_context(config: Config | None = None) -> ApiContext:
    """Initialize API context with all dependencies.

    This should be called once during application startup.

    Args:
        config: Optional pre-loaded configuration. If None, loads from file.

    Returns:
        ApiContext: Initialized context with all controllers
    """
    # Load configuration if not provided
    if config is None:
        config = ConfigManager.load()
    notes_repository = FileNotesRepository()

    # Initialize HolidayChecker if country is configured
    holiday_checker = None
    if config.region.country:
        with suppress(ImportError, NotImplementedError):
            holiday_checker = HolidayChecker(config.region.country)

    # Initialize repository using factory based on storage config
    repository = RepositoryFactory.create(config.storage)

    # Initialize loggers for each controller
    query_logger = StandardLogger("taskdog_core.controllers.query_controller")
    lifecycle_logger = StandardLogger(
        "taskdog_core.controllers.task_lifecycle_controller"
    )
    relationship_logger = StandardLogger(
        "taskdog_core.controllers.task_relationship_controller"
    )
    analytics_logger = StandardLogger(
        "taskdog_core.controllers.task_analytics_controller"
    )
    crud_logger = StandardLogger("taskdog_core.controllers.task_crud_controller")

    # Initialize controllers with loggers
    query_controller = QueryController(repository, notes_repository, query_logger)
    lifecycle_controller = TaskLifecycleController(repository, config, lifecycle_logger)
    relationship_controller = TaskRelationshipController(
        repository, config, relationship_logger
    )
    analytics_controller = TaskAnalyticsController(
        repository, config, holiday_checker, analytics_logger
    )
    crud_controller = TaskCrudController(
        repository, notes_repository, config, crud_logger
    )

    return ApiContext(
        repository=repository,
        config=config,
        notes_repository=notes_repository,
        query_controller=query_controller,
        lifecycle_controller=lifecycle_controller,
        relationship_controller=relationship_controller,
        analytics_controller=analytics_controller,
        crud_controller=crud_controller,
        holiday_checker=holiday_checker,
    )


def get_api_context() -> ApiContext:
    """Get the API context instance.

    This is the main dependency function used by FastAPI endpoints.

    Returns:
        ApiContext: The global API context instance

    Raises:
        RuntimeError: If context has not been initialized
    """
    if _api_context is None:
        raise RuntimeError(
            "API context not initialized. Call initialize_api_context() first."
        )
    return _api_context


def set_api_context(context: ApiContext) -> None:
    """Set the global API context instance.

    Args:
        context: ApiContext instance to set globally
    """
    global _api_context
    _api_context = context


# Dependency type aliases for cleaner endpoint signatures
ApiContextDep = Annotated[ApiContext, Depends(get_api_context)]


# Individual controller dependencies
def get_query_controller(context: ApiContextDep) -> QueryController:
    """Get query controller from context."""
    return context.query_controller


def get_lifecycle_controller(context: ApiContextDep) -> TaskLifecycleController:
    """Get lifecycle controller from context."""
    return context.lifecycle_controller


def get_relationship_controller(context: ApiContextDep) -> TaskRelationshipController:
    """Get relationship controller from context."""
    return context.relationship_controller


def get_analytics_controller(context: ApiContextDep) -> TaskAnalyticsController:
    """Get analytics controller from context."""
    return context.analytics_controller


def get_crud_controller(context: ApiContextDep) -> TaskCrudController:
    """Get CRUD controller from context."""
    return context.crud_controller


def get_repository(context: ApiContextDep) -> TaskRepository:
    """Get task repository from context."""
    return context.repository


def get_notes_repository(context: ApiContextDep) -> NotesRepository:
    """Get notes repository from context."""
    return context.notes_repository


def get_config(context: ApiContextDep) -> Config:
    """Get configuration from context."""
    return context.config


def get_holiday_checker(context: ApiContextDep) -> IHolidayChecker | None:
    """Get holiday checker from context (may be None)."""
    return context.holiday_checker


def get_connection_manager() -> ConnectionManager:
    """Get the global ConnectionManager instance for WebSocket connections.

    This function provides a singleton ConnectionManager instance that manages
    all active WebSocket connections and handles broadcasting events.

    Returns:
        ConnectionManager: The global connection manager instance

    Note:
        The instance is lazily initialized on first access and reused
        for all subsequent calls.
    """
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager


# Typed dependencies for endpoint signatures
QueryControllerDep = Annotated[QueryController, Depends(get_query_controller)]
LifecycleControllerDep = Annotated[
    TaskLifecycleController, Depends(get_lifecycle_controller)
]
RelationshipControllerDep = Annotated[
    TaskRelationshipController, Depends(get_relationship_controller)
]
AnalyticsControllerDep = Annotated[
    TaskAnalyticsController, Depends(get_analytics_controller)
]
CrudControllerDep = Annotated[TaskCrudController, Depends(get_crud_controller)]
RepositoryDep = Annotated[TaskRepository, Depends(get_repository)]
NotesRepositoryDep = Annotated[NotesRepository, Depends(get_notes_repository)]
ConfigDep = Annotated[Config, Depends(get_config)]
HolidayCheckerDep = Annotated[IHolidayChecker | None, Depends(get_holiday_checker)]
ConnectionManagerDep = Annotated[ConnectionManager, Depends(get_connection_manager)]


def get_broadcast_helper(
    manager: ConnectionManagerDep,
    background_tasks: BackgroundTasks,
) -> BroadcastHelper:
    """Get a BroadcastHelper instance for scheduling WebSocket broadcasts.

    Args:
        manager: ConnectionManager instance
        background_tasks: FastAPI background tasks

    Returns:
        BroadcastHelper: Helper for scheduling broadcasts
    """
    return BroadcastHelper(manager, background_tasks)


BroadcastHelperDep = Annotated[BroadcastHelper, Depends(get_broadcast_helper)]
