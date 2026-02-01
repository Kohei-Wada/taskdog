"""Mutation builders for constructing database write operations.

This module provides builder classes for INSERT, UPDATE, and DELETE operations
following the Command pattern. These builders handle write operations (mutations)
while TaskQueryBuilder handles read operations (queries), implementing CQRS
(Command Query Responsibility Segregation) pattern.

The mutation builders:
- TaskInsertBuilder: Handles INSERT operations for new tasks
- TaskUpdateBuilder: Handles UPDATE operations for existing tasks
- TaskDeleteBuilder: Handles DELETE operations for tasks
- TaskTagRelationshipBuilder: Manages task-tag many-to-many relationships
- DailyAllocationBuilder: Manages normalized daily allocation records
"""

from taskdog_core.infrastructure.persistence.database.mutation_builders.daily_allocation_builder import (
    DailyAllocationBuilder,
)
from taskdog_core.infrastructure.persistence.database.mutation_builders.task_delete_builder import (
    TaskDeleteBuilder,
)
from taskdog_core.infrastructure.persistence.database.mutation_builders.task_insert_builder import (
    TaskInsertBuilder,
)
from taskdog_core.infrastructure.persistence.database.mutation_builders.task_tag_relationship_builder import (
    TaskTagRelationshipBuilder,
)
from taskdog_core.infrastructure.persistence.database.mutation_builders.task_update_builder import (
    TaskUpdateBuilder,
)

__all__ = [
    "DailyAllocationBuilder",
    "TaskDeleteBuilder",
    "TaskInsertBuilder",
    "TaskTagRelationshipBuilder",
    "TaskUpdateBuilder",
]
