"""FastAPI dependency injection functions."""

from contextlib import suppress
from typing import Annotated

from fastapi import BackgroundTasks, Depends, FastAPI, Request, WebSocket

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


def get_api_context(request: Request) -> ApiContext:
    """Get the API context from app.state.

    This is the main dependency function used by FastAPI endpoints.

    Args:
        request: FastAPI request object (injected automatically)

    Returns:
        ApiContext: The API context instance from app.state

    Raises:
        RuntimeError: If context has not been initialized
    """
    context: ApiContext | None = getattr(request.app.state, "api_context", None)
    if context is None:
        raise RuntimeError(
            "API context not initialized. Ensure lifespan sets app.state.api_context."
        )
    return context


def set_api_context(app: FastAPI, context: ApiContext) -> None:
    """Set the API context on app.state.

    This is primarily used for testing to inject mock contexts.

    Args:
        app: FastAPI application instance
        context: ApiContext instance to store in app.state
    """
    app.state.api_context = context


def reset_app_state(app: FastAPI) -> None:
    """Reset app.state for testing.

    Args:
        app: FastAPI application instance
    """
    if hasattr(app.state, "api_context"):
        delattr(app.state, "api_context")
    if hasattr(app.state, "connection_manager"):
        delattr(app.state, "connection_manager")


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


def get_connection_manager(request: Request) -> ConnectionManager:
    """Get the ConnectionManager instance from app.state for HTTP endpoints.

    This function provides access to the ConnectionManager instance that manages
    all active WebSocket connections and handles broadcasting events.

    Args:
        request: FastAPI request object (injected automatically)

    Returns:
        ConnectionManager: The connection manager instance from app.state

    Note:
        The instance is lazily initialized on first access if not already
        set in app.state (e.g., by lifespan).
    """
    if not hasattr(request.app.state, "connection_manager"):
        request.app.state.connection_manager = ConnectionManager()
    manager: ConnectionManager = request.app.state.connection_manager
    return manager


def get_connection_manager_ws(websocket: WebSocket) -> ConnectionManager:
    """Get the ConnectionManager instance from app.state for WebSocket endpoints.

    This is the WebSocket-specific version of get_connection_manager.
    WebSocket endpoints cannot use Request, so we access app.state via websocket.app.

    Args:
        websocket: FastAPI WebSocket object (injected automatically)

    Returns:
        ConnectionManager: The connection manager instance from app.state

    Note:
        The instance is lazily initialized on first access if not already
        set in app.state (e.g., by lifespan).
    """
    if not hasattr(websocket.app.state, "connection_manager"):
        websocket.app.state.connection_manager = ConnectionManager()
    manager: ConnectionManager = websocket.app.state.connection_manager
    return manager


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
ConnectionManagerWsDep = Annotated[
    ConnectionManager, Depends(get_connection_manager_ws)
]


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
