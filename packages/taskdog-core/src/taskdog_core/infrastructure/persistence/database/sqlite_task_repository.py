"""SQLite-based implementation of TaskRepository using SQLAlchemy.

This repository provides database persistence for tasks using SQLite and
SQLAlchemy 2.0 ORM. It implements the TaskRepository interface with full
ACID transaction support.

Phase 2 (Issue 228): Tags are now stored in normalized tables (tags/task_tags).
The repository uses TagResolver to manage tag relationships when saving tasks.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Any

from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import sessionmaker

from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.repositories.task_repository import TaskRepository
from taskdog_core.infrastructure.persistence.database.migration_runner import (
    run_migrations,
)
from taskdog_core.infrastructure.persistence.database.models import (
    TagModel,
    TaskModel,
    TaskTagModel,
)
from taskdog_core.infrastructure.persistence.database.mutation_builders import (
    TaskDeleteBuilder,
    TaskInsertBuilder,
    TaskTagRelationshipBuilder,
    TaskUpdateBuilder,
)
from taskdog_core.infrastructure.persistence.database.query_builders import (
    TaskQueryBuilder,
)
from taskdog_core.infrastructure.persistence.mappers.tag_resolver import TagResolver
from taskdog_core.infrastructure.persistence.mappers.task_db_mapper import TaskDbMapper

if TYPE_CHECKING:
    from taskdog_core.domain.services.time_provider import ITimeProvider


class SqliteTaskRepository(TaskRepository):
    """SQLite implementation of TaskRepository using SQLAlchemy ORM.

    This repository:
    - Uses SQLite database for persistence
    - Provides ACID transaction guarantees
    - Implements connection pooling via SQLAlchemy engine
    - Uses TaskDbMapper for entity-model conversion
    """

    def __init__(
        self,
        database_url: str,
        mapper: TaskDbMapper | None = None,
        time_provider: ITimeProvider | None = None,
    ):
        """Initialize the repository with a SQLite database.

        Args:
            database_url: SQLAlchemy database URL (e.g., "sqlite:///path/to/db.sqlite")
            mapper: TaskDbMapper instance. If None, creates a new instance.
            time_provider: Provider for current time. Defaults to SystemTimeProvider.
        """
        self.database_url = database_url
        self.mapper = mapper or TaskDbMapper()
        if time_provider is None:
            from taskdog_core.infrastructure.time_provider import SystemTimeProvider

            time_provider = SystemTimeProvider()
        self._time_provider = time_provider

        # Create engine with SQLite-specific optimizations
        self.engine = create_engine(
            database_url,
            echo=False,  # Set to True for SQL query debugging
            # SQLite-specific settings
            connect_args={"check_same_thread": False},  # Allow multi-threading
        )

        # Configure SQLite pragmas for concurrency (Issue #226)
        @event.listens_for(self.engine, "connect")  # type: ignore[no-untyped-call]
        def set_sqlite_pragma(dbapi_connection: Any, _: Any) -> None:
            cursor = dbapi_connection.cursor()
            try:
                # WAL mode enables concurrent readers during writes
                cursor.execute("PRAGMA journal_mode=WAL")
                # 30 second timeout for lock acquisition
                cursor.execute("PRAGMA busy_timeout=30000")
                # Good balance between safety and performance with WAL
                cursor.execute("PRAGMA synchronous=NORMAL")
            finally:
                cursor.close()

        # Create sessionmaker for managing database sessions
        self.Session = sessionmaker(bind=self.engine)

        # Run database migrations
        run_migrations(self.engine)

    def get_all(self) -> list[Task]:
        """Retrieve all tasks from database.

        Returns:
            List of all tasks
        """
        with self.Session() as session:
            stmt = select(TaskModel)
            models = session.scalars(stmt).all()
            return [self.mapper.from_model(model) for model in models]

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
            stmt = select(TaskModel).where(TaskModel.id.in_(task_ids))  # type: ignore[attr-defined]
            models = session.scalars(stmt).all()
            return {model.id: self.mapper.from_model(model) for model in models}

    def get_filtered(
        self,
        include_archived: bool = True,
        status: TaskStatus | None = None,
        tags: list[str] | None = None,
        match_all_tags: bool = False,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[Task]:
        """Retrieve tasks with SQL WHERE clauses for efficient filtering.

        This method applies filters at the database level using SQL WHERE clauses,
        significantly improving performance compared to fetching all tasks and
        filtering in Python.

        Args:
            include_archived: If False, exclude archived tasks (default: True)
            status: Filter by task status (default: None, no status filter)
            tags: Filter by tags with OR logic (default: None, no tag filter)
            match_all_tags: If True, require all tags (AND logic); if False, any tag (OR logic)
            start_date: Filter tasks with any date >= start_date (default: None)
            end_date: Filter tasks with any date <= end_date (default: None)

        Returns:
            List of tasks matching the filter criteria

        Note:
            - Date filtering checks deadline, planned_start, planned_end, actual_start, actual_end
            - Tag filtering uses SQL JOIN for efficiency (Phase 3)
            - Archived filter uses indexed is_archived column
            - Status filter uses indexed status column
            - Uses TaskQueryBuilder to construct the SQL query
        """
        with self.Session() as session:
            # Build query using TaskQueryBuilder (eliminates duplication with count_tasks)
            stmt = (
                TaskQueryBuilder(select(TaskModel))
                .with_archived_filter(include_archived)
                .with_status_filter(status)
                .with_tag_filter(tags, match_all_tags)
                .with_date_filter(start_date, end_date)
                .build()
            )

            # Execute query
            models = session.scalars(stmt).all()
            return [self.mapper.from_model(model) for model in models]

    def count_tasks(
        self,
        include_archived: bool = True,
        status: TaskStatus | None = None,
        tags: list[str] | None = None,
        match_all_tags: bool = False,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> int:
        """Count tasks matching filter criteria using SQL COUNT for efficiency.

        This method uses SQL COUNT(*) instead of loading all tasks into memory,
        providing significant performance improvements for large datasets.

        Args:
            include_archived: If False, exclude archived tasks (default: True)
            status: Filter by task status (default: None, no status filter)
            tags: Filter by tags (default: None, no tag filter)
            match_all_tags: If True, require all tags (AND logic); if False, any tag (OR logic)
            start_date: Filter tasks with any date >= start_date (default: None)
            end_date: Filter tasks with any date <= end_date (default: None)

        Returns:
            Number of tasks matching the filter criteria

        Note:
            Uses the same filter logic as get_filtered() for consistency.
            Performance: O(1) index lookups vs O(n) task loading + deserialization.
            Uses TaskQueryBuilder to construct the SQL query (same as get_filtered).
        """
        with self.Session() as session:
            # Build count query using TaskQueryBuilder (eliminates duplication with get_filtered)
            stmt = (
                TaskQueryBuilder(select(func.count(TaskModel.id)))
                .with_archived_filter(include_archived)
                .with_status_filter(status)
                .with_tag_filter(tags, match_all_tags)
                .with_date_filter(start_date, end_date)
                .build()
            )

            # Execute count query
            count = session.scalar(stmt)
            return count or 0

    def count_tasks_with_tags(self) -> int:
        """Count tasks that have at least one tag using SQL COUNT.

        This method uses SQL aggregation instead of loading all tasks into memory,
        providing significant performance improvements.

        Returns:
            Number of tasks with at least one tag

        Note:
            Uses SQL COUNT(DISTINCT task_id) for efficiency.
            Performance: O(1) aggregation vs O(n) task loading + iteration.
        """
        with self.Session() as session:
            # SQL: SELECT COUNT(DISTINCT task_id) FROM task_tags
            stmt = select(func.count(func.distinct(TaskTagModel.task_id)))
            count = session.scalar(stmt)
            return count or 0

    def save(self, task: Task) -> None:
        """Save a task (create new or update existing).

        Uses mutation builders to handle INSERT/UPDATE operations and
        tag relationship management.

        Args:
            task: The task to save
        """
        with self.Session() as session:
            # Create builders for this session
            tag_resolver = TagResolver(session)
            insert_builder = TaskInsertBuilder(session, self.mapper)
            update_builder = TaskUpdateBuilder(session, self.mapper)
            tag_builder = TaskTagRelationshipBuilder(session, tag_resolver)

            # Check if task exists
            existing_model = session.get(TaskModel, task.id)

            if existing_model:
                # Update existing task
                update_builder.update_task(existing_model, task)
            else:
                # Insert new task
                existing_model = insert_builder.insert_task(task)

            # Sync tag relationships
            tag_builder.sync_task_tags(existing_model, task.tags)

            session.commit()

    def save_all(self, tasks: list[Task]) -> None:
        """Save multiple tasks in a single transaction.

        Uses mutation builders to handle bulk INSERT/UPDATE operations and
        tag relationship management.

        Args:
            tasks: List of tasks to save
        """
        if not tasks:
            return

        with self.Session() as session:
            # Create builders for this session
            tag_resolver = TagResolver(session)
            insert_builder = TaskInsertBuilder(session, self.mapper)
            update_builder = TaskUpdateBuilder(session, self.mapper)
            tag_builder = TaskTagRelationshipBuilder(session, tag_resolver)

            # Bulk fetch existing tasks to avoid N+1 queries
            existing_ids = [t.id for t in tasks if t.id is not None]
            existing_models = {}
            if existing_ids:
                stmt = select(TaskModel).where(TaskModel.id.in_(existing_ids))  # type: ignore[attr-defined]
                existing_models = {m.id: m for m in session.scalars(stmt).all()}

            for task in tasks:
                # Check for existing task only if task has an ID
                existing_model = (
                    existing_models.get(task.id) if task.id is not None else None
                )

                if existing_model:
                    # Update existing task
                    update_builder.update_task(existing_model, task)
                else:
                    # Insert new task
                    existing_model = insert_builder.insert_task(task)

                # Sync tag relationships
                tag_builder.sync_task_tags(existing_model, task.tags)

            session.commit()

    def delete(self, task_id: int) -> None:
        """Delete a task by its ID.

        Uses TaskDeleteBuilder to handle DELETE operation.

        Args:
            task_id: The ID of the task to delete
        """
        with self.Session() as session:
            delete_builder = TaskDeleteBuilder(session)
            delete_builder.delete_task(task_id)
            session.commit()

    def create(self, name: str, priority: int, **kwargs: Any) -> Task:
        """Create a new task with auto-generated ID and save it.

        Uses SQLite AUTOINCREMENT to assign IDs atomically, avoiding race
        conditions in concurrent scenarios (Issue #226).

        Args:
            name: Task name
            priority: Task priority
            **kwargs: Additional task fields

        Returns:
            Created task with database-assigned ID
        """
        now = self._time_provider.now()

        # Create task without ID - database will assign via AUTOINCREMENT
        task = Task(
            id=None,
            name=name,
            priority=priority,
            created_at=now,
            updated_at=now,
            **kwargs,
        )

        with self.Session() as session:
            # Create builders for this session
            tag_resolver = TagResolver(session)
            insert_builder = TaskInsertBuilder(session, self.mapper)
            tag_builder = TaskTagRelationshipBuilder(session, tag_resolver)

            # Insert task (flush assigns ID via AUTOINCREMENT)
            model = insert_builder.insert_task(task)

            # Sync tag relationships
            tag_builder.sync_task_tags(model, task.tags)

            session.commit()

            # Return task with assigned ID
            return self.mapper.from_model(model)

    def get_tag_counts(self) -> dict[str, int]:
        """Get all tags with their task counts using SQL aggregation.

        Phase 3 (Issue 228): Optimized query using SQL COUNT() and GROUP BY
        instead of loading all tasks into memory.

        Returns:
            Dictionary mapping tag names to task counts (non-zero counts only)

        Example:
            >>> repo.get_tag_counts()
            {'urgent': 5, 'backend': 3, 'frontend': 2}
        """
        with self.Session() as session:
            # SQL: SELECT tags.name, COUNT(task_tags.task_id)
            #      FROM tags LEFT JOIN task_tags ON tags.id = task_tags.tag_id
            #      GROUP BY tags.id, tags.name
            stmt = (
                select(TagModel.name, func.count(TaskTagModel.task_id))
                .outerjoin(TaskTagModel, TagModel.id == TaskTagModel.tag_id)
                .group_by(TagModel.id, TagModel.name)
            )

            results = session.execute(stmt).all()

            # Filter out tags with zero tasks
            return {name: count for name, count in results if count > 0}

    def get_task_ids_by_tags(
        self, tags: list[str], match_all: bool = False
    ) -> list[int]:
        """Get task IDs that match the specified tags using SQL JOIN.

        Phase 3 (Issue 228): Optimized query using SQL JOIN instead of
        loading all tasks into memory and filtering in Python.

        Args:
            tags: List of tag names to filter by
            match_all: If True, task must have ALL tags (AND logic).
                      If False, task must have at least ONE tag (OR logic).

        Returns:
            List of task IDs matching the tag filter

        Example:
            >>> # OR logic: tasks with 'urgent' OR 'backend'
            >>> repo.get_task_ids_by_tags(['urgent', 'backend'], match_all=False)
            [1, 2, 5, 7]

            >>> # AND logic: tasks with 'urgent' AND 'backend'
            >>> repo.get_task_ids_by_tags(['urgent', 'backend'], match_all=True)
            [2, 5]
        """
        if not tags:
            # No filter: return all task IDs
            with self.Session() as session:
                stmt = select(TaskModel.id)
                return list(session.scalars(stmt).all())

        with self.Session() as session:
            if match_all:
                # AND logic: task must have ALL specified tags
                # SQL: SELECT tasks.id FROM tasks
                #      JOIN task_tags ON tasks.id = task_tags.task_id
                #      JOIN tags ON task_tags.tag_id = tags.id
                #      WHERE tags.name IN (...)
                #      GROUP BY tasks.id
                #      HAVING COUNT(DISTINCT tags.name) = len(unique_tags)
                # Note: Use len(set(tags)) to handle duplicate tags in input
                unique_tag_count = len(set(tags))
                stmt = (
                    select(TaskModel.id)
                    .join(TaskTagModel, TaskModel.id == TaskTagModel.task_id)
                    .join(TagModel, TaskTagModel.tag_id == TagModel.id)
                    .where(TagModel.name.in_(tags))  # type: ignore[attr-defined]
                    .group_by(TaskModel.id)
                    .having(
                        func.count(func.distinct(TagModel.name)) == unique_tag_count
                    )
                )
            else:
                # OR logic: task must have at least ONE specified tag
                # SQL: SELECT DISTINCT tasks.id FROM tasks
                #      JOIN task_tags ON tasks.id = task_tags.task_id
                #      JOIN tags ON task_tags.tag_id = tags.id
                #      WHERE tags.name IN (...)
                stmt = (
                    select(TaskModel.id)
                    .join(TaskTagModel, TaskModel.id == TaskTagModel.task_id)
                    .join(TagModel, TaskTagModel.tag_id == TagModel.id)
                    .where(TagModel.name.in_(tags))  # type: ignore[attr-defined]
                    .distinct()
                )

            return list(session.scalars(stmt).all())

    def close(self) -> None:
        """Close database connections and clean up resources.

        Should be called when the repository is no longer needed.
        """
        self.engine.dispose()
