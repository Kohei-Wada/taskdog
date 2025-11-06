"""API routers for FastAPI endpoints."""

from presentation.api.routers.analytics import router as analytics_router
from presentation.api.routers.lifecycle import router as lifecycle_router
from presentation.api.routers.relationships import router as relationships_router
from presentation.api.routers.tasks import router as tasks_router

__all__ = [
    "analytics_router",
    "lifecycle_router",
    "relationships_router",
    "tasks_router",
]
