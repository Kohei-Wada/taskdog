"""SQLite-based implementation of TaskRepository using SQLAlchemy.

This repository provides database persistence for tasks using SQLite and
SQLAlchemy 2.0 ORM. It implements the TaskRepository interface with full
ACID transaction support.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from taskdog_core.domain.entities.task import Task
from taskdog_core.domain.repositories.task_repository import TaskRepository
from taskdog_core.infrastructure.persistence.database.models.task_model import (
    Base,
    TaskModel,
)
from taskdog_core.infrastructure.persistence.mappers.task_db_mapper import TaskDbMapper


class SqliteTaskRepository(TaskRepository):
    """SQLite implementation of TaskRepository using SQLAlchemy ORM.

    This repository:
    - Uses SQLite database for persistence
    - Provides ACID transaction guarantees
    - Implements connection pooling via SQLAlchemy engine
    - Maintains in-memory cache for get_all() performance
    - Uses TaskDbMapper for entity-model conversion
    """

    def __init__(self, database_url: str, mapper: TaskDbMapper | None = None):
        """Initialize the repository with a SQLite database.

        Args:
            database_url: SQLAlchemy database URL (e.g., "sqlite:///path/to/db.sqlite")
            mapper: TaskDbMapper instance. If None, creates a new instance.
        """
        self.database_url = database_url
        self.mapper = mapper or TaskDbMapper()

        # Create engine with SQLite-specific optimizations
        self.engine = create_engine(
            database_url,
            echo=False,  # Set to True for SQL query debugging
            # SQLite-specific settings
            connect_args={"check_same_thread": False},  # Allow multi-threading
        )

        # Create sessionmaker for managing database sessions
        self.Session = sessionmaker(bind=self.engine)

        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)

        # Initialize in-memory cache
        self._cache: list[Task] | None = None

    def get_all(self) -> list[Task]:
        """Retrieve all tasks from database.

        Uses in-memory cache for performance. Cache is invalidated on write operations.

        Returns:
            List of all tasks
        """
        if self._cache is not None:
            return self._cache

        with self.Session() as session:
            stmt = select(TaskModel)
            models = session.scalars(stmt).all()
            self._cache = [self.mapper.from_model(model) for model in models]
            return self._cache

    def get_by_id(self, task_id: int) -> Task | None:
        """Retrieve a task by its ID.

        Args:
            task_id: The ID of the task to retrieve

        Returns:
            The task if found, None otherwise
        """
        with self.Session() as session:
            model = session.get(TaskModel, task_id)
            if model is None:
                return None
            return self.mapper.from_model(model)

    def get_by_ids(self, task_ids: list[int]) -> dict[int, Task]:
        """Retrieve multiple tasks by their IDs in a single query.

        Args:
            task_ids: List of task IDs to retrieve

        Returns:
            Dictionary mapping task IDs to Task objects
        """
        if not task_ids:
            return {}

        with self.Session() as session:
            stmt = select(TaskModel).where(TaskModel.id.in_(task_ids))
            models = session.scalars(stmt).all()
            return {model.id: self.mapper.from_model(model) for model in models}

    def save(self, task: Task) -> None:
        """Save a task (create new or update existing).

        Args:
            task: The task to save
        """
        with self.Session() as session:
            # Check if task exists
            existing_model = session.get(TaskModel, task.id)

            if existing_model:
                # Update existing task
                self.mapper.update_model(existing_model, task)
                # Update timestamp
                existing_model.updated_at = datetime.now()
            else:
                # Create new task
                new_model = self.mapper.to_model(task)
                session.add(new_model)

            session.commit()

        # Invalidate cache
        self._cache = None

    def save_all(self, tasks: list[Task]) -> None:
        """Save multiple tasks in a single transaction.

        Args:
            tasks: List of tasks to save
        """
        if not tasks:
            return

        with self.Session() as session:
            for task in tasks:
                existing_model = session.get(TaskModel, task.id)

                if existing_model:
                    # Update existing
                    self.mapper.update_model(existing_model, task)
                    existing_model.updated_at = datetime.now()
                else:
                    # Create new
                    new_model = self.mapper.to_model(task)
                    session.add(new_model)

            session.commit()

        # Invalidate cache
        self._cache = None

    def delete(self, task_id: int) -> None:
        """Delete a task by its ID.

        Args:
            task_id: The ID of the task to delete
        """
        with self.Session() as session:
            model = session.get(TaskModel, task_id)
            if model:
                session.delete(model)
                session.commit()

        # Invalidate cache
        self._cache = None

    def generate_next_id(self) -> int:
        """Generate the next available task ID.

        Returns:
            The next available ID (max_id + 1, or 1 if no tasks exist)
        """
        with self.Session() as session:
            stmt = select(TaskModel.id).order_by(TaskModel.id.desc()).limit(1)
            result = session.scalar(stmt)
            return (result + 1) if result is not None else 1

    def create(self, name: str, priority: int, **kwargs: Any) -> Task:
        """Create a new task with auto-generated ID and save it.

        Args:
            name: Task name
            priority: Task priority
            **kwargs: Additional task fields

        Returns:
            Created task with ID assigned
        """
        task_id = self.generate_next_id()
        now = datetime.now()

        task = Task(
            id=task_id,
            name=name,
            priority=priority,
            created_at=now,
            updated_at=now,
            **kwargs,
        )

        self.save(task)
        return task

    def reload(self) -> None:
        """Reload tasks from database by invalidating cache.

        The next get_all() call will fetch fresh data from the database.
        """
        self._cache = None

    def close(self) -> None:
        """Close database connections and clean up resources.

        Should be called when the repository is no longer needed.
        """
        self.engine.dispose()
