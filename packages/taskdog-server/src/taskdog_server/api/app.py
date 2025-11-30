"""FastAPI application factory and configuration."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from taskdog_core.shared.config_manager import ConfigManager
from taskdog_server.api.dependencies import (
    initialize_api_context,
    set_api_context,
    verify_api_key,
)
from taskdog_server.api.middleware import LoggingMiddleware
from taskdog_server.api.routers import (
    analytics_router,
    lifecycle_router,
    notes_router,
    relationships_router,
    tasks_router,
    websocket_router,
)
from taskdog_server.infrastructure.logging.config import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """FastAPI lifespan context manager.

    Initializes logging and API context on startup and cleans up on shutdown.

    Raises:
        RuntimeError: If API key is not configured
    """
    # Startup: Configure logging first
    configure_logging()

    # Initialize API context
    api_context = initialize_api_context()

    # Validate API key is configured
    if not api_context.config.api.api_key:
        raise RuntimeError(
            "API key is required. Set TASKDOG_API_KEY environment variable "
            "or api_key in [api] section of config.toml"
        )

    set_api_context(api_context)

    yield

    # Shutdown: Cleanup (if needed in the future)
    pass


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance
    """
    app = FastAPI(
        title="Taskdog API",
        description="Task management API with scheduling, dependencies, and analytics",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Add logging middleware (should be first to log all requests)
    app.add_middleware(LoggingMiddleware)

    # Load configuration to get CORS settings
    config = ConfigManager.load()

    # Configure CORS with settings from config file or defaults
    # Default origins: localhost:3000, localhost:8000, 127.0.0.1:3000, 127.0.0.1:8000
    # Can be overridden in config.toml under [api] section with cors_origins = [...]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.api.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API key authentication dependency for protected routes
    api_key_deps = [Depends(verify_api_key)]

    # Register routers with API key authentication
    app.include_router(
        tasks_router,
        prefix="/api/v1/tasks",
        tags=["tasks"],
        dependencies=api_key_deps,
    )
    app.include_router(
        lifecycle_router,
        prefix="/api/v1/tasks",
        tags=["lifecycle"],
        dependencies=api_key_deps,
    )
    app.include_router(
        relationships_router,
        prefix="/api/v1/tasks",
        tags=["relationships"],
        dependencies=api_key_deps,
    )
    app.include_router(
        notes_router,
        prefix="/api/v1/tasks",
        tags=["notes"],
        dependencies=api_key_deps,
    )
    app.include_router(
        analytics_router,
        prefix="/api/v1",
        tags=["analytics"],
        dependencies=api_key_deps,
    )
    app.include_router(
        websocket_router,
        tags=["websocket"],
        dependencies=api_key_deps,
    )

    @app.get("/")
    async def root() -> dict[str, str]:
        """Root endpoint."""
        return {"message": "Taskdog API", "version": "1.0.0"}

    @app.get("/health")
    async def health() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "ok"}

    return app


# Create app instance
app = create_app()
