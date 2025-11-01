"""CLI context for dependency injection."""

from dataclasses import dataclass

from domain.repositories.notes_repository import NotesRepository
from domain.repositories.task_repository import TaskRepository
from domain.services.time_tracker import TimeTracker
from presentation.console.console_writer import ConsoleWriter
from presentation.controllers.query_controller import QueryController
from presentation.controllers.task_controller import TaskController
from shared.config_manager import Config


@dataclass
class CliContext:
    """Context object for CLI commands containing shared dependencies.

    Attributes:
        console_writer: Console writer for output
        repository: Task repository for data access
        time_tracker: Time tracker for recording timestamps
        config: Application configuration
        notes_repository: Notes repository for notes file operations
        task_controller: Controller for task write operations
        query_controller: Controller for task read operations
    """

    console_writer: ConsoleWriter
    repository: TaskRepository
    time_tracker: TimeTracker
    config: Config
    notes_repository: NotesRepository
    task_controller: TaskController
    query_controller: QueryController
