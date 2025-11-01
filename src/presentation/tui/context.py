"""TUI context for dependency injection."""

from dataclasses import dataclass

from domain.repositories.notes_repository import NotesRepository
from presentation.controllers.query_controller import QueryController
from presentation.controllers.task_analytics_controller import TaskAnalyticsController
from presentation.controllers.task_controller import TaskController
from presentation.controllers.task_crud_controller import TaskCrudController
from presentation.controllers.task_lifecycle_controller import TaskLifecycleController
from presentation.controllers.task_relationship_controller import (
    TaskRelationshipController,
)
from shared.config_manager import Config


@dataclass
class TUIContext:
    """Context object holding TUI dependencies.

    This dataclass provides a clean way to pass dependencies to TUI commands
    without coupling them to the entire app instance.

    Attributes:
        config: Application configuration
        notes_repository: Notes repository for notes file operations
        task_controller: Controller for task write operations (legacy, will be deprecated)
        query_controller: Controller for task read operations
        lifecycle_controller: Controller for task lifecycle operations (start, complete, etc.)
        relationship_controller: Controller for task relationships (dependencies, tags, hours)
        analytics_controller: Controller for analytics operations (statistics, optimization)
        crud_controller: Controller for CRUD operations (create, update, archive, etc.)
    """

    config: Config
    notes_repository: NotesRepository
    task_controller: TaskController
    query_controller: QueryController
    lifecycle_controller: TaskLifecycleController
    relationship_controller: TaskRelationshipController
    analytics_controller: TaskAnalyticsController
    crud_controller: TaskCrudController
