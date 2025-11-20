"""SQLite-based implementation of TaskRepository using SQLAlchemy.

This repository provides database persistence for tasks using SQLite and
SQLAlchemy 2.0 ORM. It implements the TaskRepository interface with full
ACID transaction support.

Phase 2 (Issue 228): Tags are now stored in normalized tables (tags/task_tags).
The repository uses TagResolver to manage tag relationships when saving tasks.
"""

from datetime import date, datetime
from typing import Any

from sqlalchemy import create_engine, func, or_, select
from sqlalchemy.orm import Session, sessionmaker

from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.repositories.task_repository import TaskRepository
from taskdog_core.infrastructure.persistence.database.models import (
    TagModel,
    TaskModel,
    TaskTagModel,
)
from taskdog_core.infrastructure.persistence.database.models.task_model import Base
from taskdog_core.infrastructure.persistence.mappers.tag_resolver import TagResolver
from taskdog_core.infrastructure.persistence.mappers.task_db_mapper import TaskDbMapper


class SqliteTaskRepository(TaskRepository):
    """SQLite implementation of TaskRepository using SQLAlchemy ORM.

    This repository:
    - Uses SQLite database for persistence
    - Provides ACID transaction guarantees
    - Implements connection pooling via SQLAlchemy engine
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
        """
        with self.Session() as session:
            stmt = select(TaskModel)

            # Filter by archived status (uses index)
            if not include_archived:
                stmt = stmt.where(TaskModel.is_archived == False)  # noqa: E712

            # Filter by status (uses index)
            if status is not None:
                stmt = stmt.where(TaskModel.status == status.value)

            # Filter by tags (uses JOIN)
            if tags:
                if match_all_tags:
                    # AND logic: task must have ALL specified tags
                    for tag in tags:
                        tag_subquery = (
                            select(TaskTagModel.task_id)
                            .join(TagModel, TaskTagModel.tag_id == TagModel.id)
                            .where(TagModel.name == tag)
                        )
                        stmt = stmt.where(TaskModel.id.in_(tag_subquery))  # type: ignore[attr-defined]
                else:
                    # OR logic: task must have ANY of the specified tags
                    tag_subquery = (
                        select(TaskTagModel.task_id)
                        .join(TagModel, TaskTagModel.tag_id == TagModel.id)
                        .where(TagModel.name.in_(tags))  # type: ignore[attr-defined]
                    )
                    stmt = stmt.where(TaskModel.id.in_(tag_subquery))  # type: ignore[attr-defined]

            # Filter by date range (checks multiple date fields)
            if start_date is not None or end_date is not None:
                date_conditions = self._build_date_filter_conditions(
                    start_date, end_date
                )
                if date_conditions:
                    stmt = stmt.where(or_(*date_conditions))

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
        """
        with self.Session() as session:
            stmt = select(func.count(TaskModel.id))

            # Filter by archived status (uses index)
            if not include_archived:
                stmt = stmt.where(TaskModel.is_archived == False)  # noqa: E712

            # Filter by status (uses index)
            if status is not None:
                stmt = stmt.where(TaskModel.status == status.value)

            # Filter by tags (uses JOIN)
            if tags:
                if match_all_tags:
                    # AND logic: task must have ALL specified tags
                    for tag in tags:
                        tag_subquery = (
                            select(TaskTagModel.task_id)
                            .join(TagModel, TaskTagModel.tag_id == TagModel.id)
                            .where(TagModel.name == tag)
                        )
                        stmt = stmt.where(TaskModel.id.in_(tag_subquery))  # type: ignore[attr-defined]
                else:
                    # OR logic: task must have ANY of the specified tags
                    tag_subquery = (
                        select(TaskTagModel.task_id)
                        .join(TagModel, TaskTagModel.tag_id == TagModel.id)
                        .where(TagModel.name.in_(tags))  # type: ignore[attr-defined]
                    )
                    stmt = stmt.where(TaskModel.id.in_(tag_subquery))  # type: ignore[attr-defined]

            # Filter by date range (checks multiple date fields)
            if start_date is not None or end_date is not None:
                date_conditions = self._build_date_filter_conditions(
                    start_date, end_date
                )
                if date_conditions:
                    stmt = stmt.where(or_(*date_conditions))

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

        Phase 2: Also manages tag relationships via TagResolver.

        Args:
            task: The task to save
        """
        with self.Session() as session:
            # Create TagResolver for this session
            tag_resolver = TagResolver(session)

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
                session.flush()  # Get the ID for tag relationships
                existing_model = new_model

            # Phase 2: Update tag relationships
            self._update_task_tags(session, existing_model, task.tags, tag_resolver)

            session.commit()

    def save_all(self, tasks: list[Task]) -> None:
        """Save multiple tasks in a single transaction.

        Phase 2: Also manages tag relationships via shared TagResolver.

        Args:
            tasks: List of tasks to save
        """
        if not tasks:
            return

        with self.Session() as session:
            # Create TagResolver for this session (shared across all tasks)
            tag_resolver = TagResolver(session)

            # Bulk fetch existing tasks to avoid N+1 queries
            existing_ids = [t.id for t in tasks if t.id is not None]
            existing_models = {}
            if existing_ids:
                stmt = select(TaskModel).where(TaskModel.id.in_(existing_ids))  # type: ignore[attr-defined]
                existing_models = {m.id: m for m in session.scalars(stmt).all()}

            for task in tasks:
                existing_model = existing_models.get(task.id)

                if existing_model:
                    # Update existing
                    self.mapper.update_model(existing_model, task)
                    existing_model.updated_at = datetime.now()
                else:
                    # Create new
                    new_model = self.mapper.to_model(task)
                    session.add(new_model)
                    session.flush()  # Get the ID for tag relationships
                    existing_model = new_model

                # Phase 2: Update tag relationships
                self._update_task_tags(session, existing_model, task.tags, tag_resolver)

            session.commit()

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

    def generate_next_id(self) -> int:
        """Generate the next available task ID.

        Returns:
            The next available ID (max_id + 1, or 1 if no tasks exist)
        """
        with self.Session() as session:
            stmt = select(TaskModel.id).order_by(TaskModel.id.desc()).limit(1)  # type: ignore[attr-defined]
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

    def _update_task_tags(
        self,
        session: Session,
        task_model: TaskModel,
        tag_names: list[str],
        tag_resolver: TagResolver,
    ) -> None:
        """Update task's tag relationships.

        Phase 2 (Issue 228): This method manages the many-to-many relationship
        between tasks and tags using the normalized schema.

        Args:
            session: SQLAlchemy session for database operations
            task_model: The TaskModel instance to update
            tag_names: List of tag names for this task
            tag_resolver: TagResolver for tag name/ID conversion

        Process:
            1. Clear existing tag relationships
            2. If tag_names is empty, we're done
            3. Convert tag names to IDs (creates tags if needed)
            4. Fetch TagModel instances for those IDs
            5. Associate them with the task via relationship
        """
        # Clear existing relationships
        task_model.tag_models.clear()  # type: ignore[attr-defined]

        if not tag_names:
            # No tags to associate
            return

        # Resolve tag names to IDs (creates new tags if needed)
        tag_ids = tag_resolver.resolve_tag_names_to_ids(tag_names)

        # Fetch TagModel instances
        stmt = select(TagModel).where(TagModel.id.in_(tag_ids))  # type: ignore[attr-defined]
        tag_models_list = session.scalars(stmt).all()

        # Preserve original order: SQL IN clause doesn't guarantee order
        tag_models_by_id = {tag.id: tag for tag in tag_models_list}
        ordered_tag_models = [tag_models_by_id[tag_id] for tag_id in tag_ids]

        # Associate tags with task (preserving order)
        # Note: SQLAlchemy will handle the task_tags junction table automatically
        task_model.tag_models.extend(ordered_tag_models)  # type: ignore[attr-defined]

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

    def _build_date_filter_conditions(
        self, start_date: date | None, end_date: date | None
    ) -> list[Any]:
        """Build SQL date filter conditions for multiple date fields.

        This helper method creates SQLAlchemy filter conditions for date range
        filtering across all date fields (deadline, planned_start, planned_end,
        actual_start, actual_end). It handles three cases for each field:
        - Both start and end dates: field.between(start_date, end_date)
        - Only start date: field >= start_date
        - Only end date: field <= end_date

        Args:
            start_date: Minimum date for filtering (inclusive), or None
            end_date: Maximum date for filtering (inclusive), or None

        Returns:
            List of SQLAlchemy filter conditions (empty if both dates are None)

        Note:
            The returned conditions should be combined with OR logic, as we want
            to match tasks where ANY of the date fields fall within the range.
        """
        date_conditions = []

        # Define all date fields to check
        date_fields = [
            TaskModel.deadline,
            TaskModel.planned_start,
            TaskModel.planned_end,
            TaskModel.actual_start,
            TaskModel.actual_end,
        ]

        # Build conditions for each date field
        for field in date_fields:
            if start_date and end_date:
                date_conditions.append(field.between(start_date, end_date))  # type: ignore[attr-defined]
            elif start_date:
                date_conditions.append(field >= start_date)  # type: ignore[operator]
            elif end_date:
                date_conditions.append(field <= end_date)  # type: ignore[operator]

        return date_conditions

    def close(self) -> None:
        """Close database connections and clean up resources.

        Should be called when the repository is no longer needed.
        """
        self.engine.dispose()
