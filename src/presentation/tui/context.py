"""TUI context for dependency injection."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from domain.repositories.notes_repository import NotesRepository
from domain.services.holiday_checker import IHolidayChecker
from presentation.controllers.query_controller import QueryController
from presentation.controllers.task_analytics_controller import TaskAnalyticsController
from presentation.controllers.task_crud_controller import TaskCrudController
from presentation.controllers.task_lifecycle_controller import TaskLifecycleController
from presentation.controllers.task_relationship_controller import (
    TaskRelationshipController,
)
from shared.config_manager import Config

if TYPE_CHECKING:
    from infrastructure.api_client import TaskdogApiClient


@dataclass
class TUIContext:
    """Context object holding TUI dependencies.

    This dataclass provides a clean way to pass dependencies to TUI commands
    without coupling them to the entire app instance.

    TUI now requires an API client connection to function.
    Local repository mode is no longer supported.

    Attributes:
        api_client: API client for server communication (required)
        config: Application configuration
        notes_repository: Notes repository (deprecated, kept for compatibility)
        query_controller: Controller for task read operations
        lifecycle_controller: Controller for task lifecycle operations (start, complete, etc.)
        relationship_controller: Controller for task relationships (dependencies, tags, hours)
        analytics_controller: Controller for analytics operations (statistics, optimization)
        crud_controller: Controller for CRUD operations (create, update, archive, etc.)
        holiday_checker: Holiday checker for workday validation (optional)
    """

    api_client: "TaskdogApiClient"
    config: Config
    notes_repository: NotesRepository
    query_controller: QueryController
    lifecycle_controller: TaskLifecycleController
    relationship_controller: TaskRelationshipController
    analytics_controller: TaskAnalyticsController
    crud_controller: TaskCrudController
    holiday_checker: IHolidayChecker | None
