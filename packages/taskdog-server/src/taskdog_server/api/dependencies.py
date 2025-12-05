"""FastAPI dependency injection functions."""

import secrets
from contextlib import suppress
from typing import Annotated

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, WebSocket
from fastapi.security import APIKeyHeader

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
from taskdog_core.domain.services.time_provider import ITimeProvider
from taskdog_core.infrastructure.holiday_checker import HolidayChecker
from taskdog_core.infrastructure.persistence.database.sqlite_audit_log_repository import (
    SqliteAuditLogRepository,
)
from taskdog_core.infrastructure.persistence.file_notes_repository import (
    FileNotesRepository,
)
from taskdog_core.infrastructure.persistence.repository_factory import RepositoryFactory
from taskdog_core.infrastructure.time_provider import SystemTimeProvider
from taskdog_core.shared.config_manager import Config, ConfigManager
from taskdog_server.api.context import ApiContext
from taskdog_server.config.server_config_manager import ServerConfig
from taskdog_server.infrastructure.audit import BackgroundAuditLogger
from taskdog_server.infrastructure.logging.standard_logger import StandardLogger
from taskdog_server.websocket.broadcaster import WebSocketEventBroadcaster
from taskdog_server.websocket.connection_manager import ConnectionManager

# API Key header definition
api_key_header = APIKeyHeader(name="X-Api-Key", auto_error=False)


def initialize_api_context(
    config: Config | None = None,
    time_provider: ITimeProvider | None = None,
) -> ApiContext:
    """Initialize API context with all dependencies.

    This should be called once during application startup.

    Args:
        config: Optional pre-loaded configuration. If None, loads from file.
        time_provider: Optional time provider. If None, uses SystemTimeProvider.

    Returns:
        ApiContext: Initialized context with all controllers
    """
    # Load configuration if not provided
    if config is None:
        config = ConfigManager.load()
    notes_repository = FileNotesRepository()

    # Initialize time provider if not provided
    if time_provider is None:
        time_provider = SystemTimeProvider()

    # Initialize HolidayChecker if country is configured
    holiday_checker = None
    if config.region.country:
        with suppress(ImportError, NotImplementedError):
            holiday_checker = HolidayChecker(config.region.country)

    # Initialize repository using factory based on storage config
    repository = RepositoryFactory.create(config.storage)

    # Initialize audit log repository (shares the same database)
    # Use the same URL resolution logic as RepositoryFactory
    if config.storage.database_url:
        audit_db_url = config.storage.database_url
    else:
        from taskdog_core.shared.xdg_utils import XDGDirectories

        data_dir = XDGDirectories.get_data_home()
        db_file = data_dir / "tasks.db"
        audit_db_url = f"sqlite:///{db_file}"
    audit_log_repository = SqliteAuditLogRepository(audit_db_url)

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
        time_provider=time_provider,
        audit_log_repository=audit_log_repository,
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


def get_time_provider(context: ApiContextDep) -> ITimeProvider:
    """Get time provider from context."""
    return context.time_provider


def get_audit_log_repository(context: ApiContextDep) -> SqliteAuditLogRepository:
    """Get audit log repository from context."""
    return context.audit_log_repository


def get_audit_logger(
    context: ApiContextDep,
    background_tasks: BackgroundTasks,
) -> BackgroundAuditLogger:
    """Get a BackgroundAuditLogger instance for non-blocking audit logging.

    Args:
        context: API context with audit log repository
        background_tasks: FastAPI background tasks for async scheduling

    Returns:
        BackgroundAuditLogger: Logger for scheduling audit log writes
    """
    return BackgroundAuditLogger(context.audit_log_repository, background_tasks)


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
TimeProviderDep = Annotated[ITimeProvider, Depends(get_time_provider)]
AuditLogRepositoryDep = Annotated[
    SqliteAuditLogRepository, Depends(get_audit_log_repository)
]
AuditLoggerDep = Annotated[BackgroundAuditLogger, Depends(get_audit_logger)]
ConnectionManagerDep = Annotated[ConnectionManager, Depends(get_connection_manager)]
ConnectionManagerWsDep = Annotated[
    ConnectionManager, Depends(get_connection_manager_ws)
]


def get_event_broadcaster(
    manager: ConnectionManagerDep,
    background_tasks: BackgroundTasks,
) -> WebSocketEventBroadcaster:
    """Get a WebSocketEventBroadcaster instance for scheduling WebSocket broadcasts.

    Args:
        manager: ConnectionManager instance
        background_tasks: FastAPI background tasks

    Returns:
        WebSocketEventBroadcaster: Broadcaster for scheduling WebSocket events
    """
    return WebSocketEventBroadcaster(manager, background_tasks)


EventBroadcasterDep = Annotated[
    WebSocketEventBroadcaster, Depends(get_event_broadcaster)
]


# Server config dependency
def get_server_config(request: Request) -> ServerConfig:
    """Get the server config from app.state.

    Args:
        request: FastAPI request object (injected automatically)

    Returns:
        ServerConfig: The server config instance from app.state

    Raises:
        RuntimeError: If server config has not been initialized
    """
    config: ServerConfig | None = getattr(request.app.state, "server_config", None)
    if config is None:
        raise RuntimeError(
            "Server config not initialized. Ensure lifespan sets app.state.server_config."
        )
    return config


def get_server_config_ws(websocket: WebSocket) -> ServerConfig:
    """Get the server config from app.state for WebSocket endpoints.

    Args:
        websocket: FastAPI WebSocket object (injected automatically)

    Returns:
        ServerConfig: The server config instance from app.state

    Raises:
        RuntimeError: If server config has not been initialized
    """
    config: ServerConfig | None = getattr(websocket.app.state, "server_config", None)
    if config is None:
        raise RuntimeError(
            "Server config not initialized. Ensure lifespan sets app.state.server_config."
        )
    return config


ServerConfigDep = Annotated[ServerConfig, Depends(get_server_config)]
ServerConfigWsDep = Annotated[ServerConfig, Depends(get_server_config_ws)]


def get_authenticated_client(
    api_key: Annotated[str | None, Depends(api_key_header)],
    server_config: ServerConfigDep,
) -> str | None:
    """Validate API key and return client name.

    Args:
        api_key: API key from X-Api-Key header
        server_config: Server configuration with auth settings

    Returns:
        Client name if authenticated, None if auth is disabled

    Raises:
        HTTPException: 401 if authentication fails
    """
    # If auth is disabled, allow all requests
    if not server_config.auth.enabled:
        return None

    # Auth is enabled but no API keys configured - reject all
    if not server_config.auth.api_keys:
        raise HTTPException(
            status_code=401,
            detail="Authentication required but no API keys configured",
        )

    # API key required
    if api_key is None:
        raise HTTPException(status_code=401, detail="API key required")

    # Validate API key using constant-time comparison to prevent timing attacks
    for entry in server_config.auth.api_keys:
        if secrets.compare_digest(entry.key, api_key):
            return entry.name

    raise HTTPException(status_code=401, detail="Invalid API key")


AuthenticatedClientDep = Annotated[str | None, Depends(get_authenticated_client)]


def validate_api_key_for_websocket(
    api_key: str | None,
    server_config: ServerConfig,
) -> str | None:
    """Validate API key for WebSocket connections.

    This is a helper function (not a FastAPI dependency) for WebSocket
    authentication where we need to validate query parameters.

    Args:
        api_key: API key from query parameter
        server_config: Server configuration with auth settings

    Returns:
        Client name if authenticated, None if auth is disabled

    Raises:
        ValueError: If authentication fails
    """
    # If auth is disabled, allow all requests
    if not server_config.auth.enabled:
        return None

    # Auth is enabled but no API keys configured - reject all
    if not server_config.auth.api_keys:
        raise ValueError("Authentication required but no API keys configured")

    # API key required
    if api_key is None:
        raise ValueError("API key required")

    # Validate API key using constant-time comparison to prevent timing attacks
    for entry in server_config.auth.api_keys:
        if secrets.compare_digest(entry.key, api_key):
            return entry.name

    raise ValueError("Invalid API key")
