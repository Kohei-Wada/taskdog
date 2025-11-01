"""TUI context for dependency injection."""

from dataclasses import dataclass

from domain.repositories.notes_repository import NotesRepository
from presentation.controllers.query_controller import QueryController
from presentation.controllers.task_controller import TaskController
from shared.config_manager import Config


@dataclass
class TUIContext:
    """Context object holding TUI dependencies.

    This dataclass provides a clean way to pass dependencies to TUI commands
    without coupling them to the entire app instance.

    Attributes:
        config: Application configuration
        notes_repository: Notes repository for notes file operations
        task_controller: Controller for task write operations
        query_controller: Controller for task read operations
    """

    config: Config
    notes_repository: NotesRepository
    task_controller: TaskController
    query_controller: QueryController
