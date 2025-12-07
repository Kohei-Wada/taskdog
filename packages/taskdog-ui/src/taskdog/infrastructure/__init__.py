"""Infrastructure layer for taskdog-ui.

This module provides the API client facade and specialized clients
for communicating with the Taskdog server.
"""

from taskdog_client import (  # type: ignore[import-not-found]
    AnalyticsClient,
    BaseApiClient,
    LifecycleClient,
    NotesClient,
    QueryClient,
    RelationshipClient,
    TaskClient,
)

from taskdog.infrastructure.api_client import TaskdogApiClient

__all__ = [
    "AnalyticsClient",
    "BaseApiClient",
    "LifecycleClient",
    "NotesClient",
    "QueryClient",
    "RelationshipClient",
    "TaskClient",
    "TaskdogApiClient",
]
