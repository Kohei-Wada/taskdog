"""Hierarchy manager service for task relationships."""

import copy
from datetime import datetime

from domain.constants import DATETIME_FORMAT
from domain.entities.task import Task
from domain.services.task_eligibility_checker import TaskEligibilityChecker


class HierarchyManager:
    """Service for managing task hierarchy relationships.

    Handles updating parent task periods and clearing unscheduled
    tasks when force_override is enabled.
    """

    def __init__(self, repository):
        """Initialize hierarchy manager.

        Args:
            repository: Task repository for hierarchy queries
        """
        self.repository = repository

    def update_parent_periods(self, all_tasks: list[Task], updated_tasks: list[Task]) -> list[Task]:
        """Update parent task periods to encompass their children.

        Args:
            all_tasks: All tasks in the system
            updated_tasks: Tasks that were updated with new schedules

        Returns:
            All tasks that were modified (updated tasks + affected parents)
        """
        # Use a dict to track modified tasks by ID to prevent duplicates
        modified_task_dict = {t.id: t for t in updated_tasks}
        task_map = {t.id: t for t in all_tasks}
        # Create map of updated tasks for easy lookup (will be updated with parent changes)
        updated_task_map = {t.id: t for t in updated_tasks}

        # Collect all parent IDs that need updating
        parent_ids_to_update = set()
        for task in updated_tasks:
            if task.parent_id:
                parent_ids_to_update.add(task.parent_id)

        # Update each parent
        while parent_ids_to_update:
            parent_id = parent_ids_to_update.pop()
            parent_task = task_map.get(parent_id)

            if not parent_task:
                continue

            # Skip archived parent tasks - they should not be updated
            if not TaskEligibilityChecker.can_be_updated_in_hierarchy(parent_task):
                continue

            # Get all children from repository
            children_from_repo = self.repository.get_children(parent_id)
            if not children_from_repo:
                continue

            # Use updated versions of children if available
            children = []
            for child in children_from_repo:
                if child.id in updated_task_map:
                    children.append(updated_task_map[child.id])
                else:
                    children.append(child)

            # Find earliest start and latest end among children with schedules
            child_starts = [
                datetime.strptime(c.planned_start, DATETIME_FORMAT)
                for c in children
                if c.planned_start
            ]
            child_ends = [
                datetime.strptime(c.planned_end, DATETIME_FORMAT) for c in children if c.planned_end
            ]

            if child_starts and child_ends:
                parent_start = min(child_starts).strftime(DATETIME_FORMAT)
                parent_end = max(child_ends).strftime(DATETIME_FORMAT)

                # Update parent if period changed
                if (
                    parent_task.planned_start != parent_start
                    or parent_task.planned_end != parent_end
                ):
                    # Create a copy of parent task
                    parent_task_copy = copy.deepcopy(parent_task)
                    parent_task_copy.planned_start = parent_start
                    parent_task_copy.planned_end = parent_end

                    # Add to modified dict (overwrites if already exists, preventing duplicates)
                    modified_task_dict[parent_task_copy.id] = parent_task_copy
                    # Update the map so nested parents can use this updated version
                    updated_task_map[parent_task_copy.id] = parent_task_copy

                    # If this parent has a parent, update it too
                    if parent_task_copy.parent_id:
                        parent_ids_to_update.add(parent_task_copy.parent_id)

        return list(modified_task_dict.values())

    def clear_unscheduled_tasks(
        self, all_tasks: list[Task], updated_tasks: list[Task]
    ) -> list[Task]:
        """Clear schedules for tasks that couldn't be scheduled with force_override.

        When force_override is True, tasks that had schedules but couldn't be
        rescheduled (e.g., due to deadline constraints) should have their old
        schedules removed to avoid inconsistency.

        Args:
            all_tasks: All tasks in the system
            updated_tasks: Tasks that were successfully scheduled

        Returns:
            Combined list of updated tasks and cleared tasks
        """
        # Build set of updated task IDs
        updated_ids = {t.id for t in updated_tasks}

        # Build parent-child map
        parent_ids = set()
        for task in all_tasks:
            if task.parent_id:
                parent_ids.add(task.parent_id)

        # Find tasks that need their schedules cleared
        cleared_tasks = []
        for task in all_tasks:
            # Skip if already updated
            if task.id in updated_ids:
                continue

            # Skip parent tasks (they don't have allocations)
            if task.id in parent_ids:
                continue

            # Skip tasks that shouldn't be rescheduled (completed/archived/in-progress)
            if not TaskEligibilityChecker.can_be_rescheduled(task):
                continue

            # Skip tasks that never had schedules
            if not task.planned_start:
                continue

            # Skip tasks without estimated_duration (they shouldn't have been scheduled)
            if not task.estimated_duration:
                continue

            # This task had a schedule but wasn't successfully rescheduled
            # Clear its schedule to avoid inconsistency
            task_copy = copy.deepcopy(task)
            task_copy.planned_start = None
            task_copy.planned_end = None
            task_copy.daily_allocations = None
            cleared_tasks.append(task_copy)

        return updated_tasks + cleared_tasks

    def update_parent_estimated_duration(self, parent_id: int) -> Task | None:
        """Update parent task's estimated_duration based on sum of children's estimates.

        Recursively updates all ancestor tasks' estimated_duration.
        Parent task's estimated_duration = sum of all children's estimated_duration.

        Args:
            parent_id: ID of the parent task to update

        Returns:
            Updated parent task if successful, None if parent not found or no children
        """
        parent_task = self.repository.get_by_id(parent_id)
        if not parent_task:
            return None

        # Skip archived parent tasks - they should not be updated
        if not TaskEligibilityChecker.can_be_updated_in_hierarchy(parent_task):
            return None

        # Get all children
        children = self.repository.get_children(parent_id)
        if not children:
            return None

        # Calculate sum of children's estimated_duration
        total_estimate = 0.0
        has_estimates = False
        for child in children:
            if child.estimated_duration is not None:
                total_estimate += child.estimated_duration
                has_estimates = True

        # Update parent's estimated_duration if children have estimates
        if has_estimates:
            parent_task_copy = copy.deepcopy(parent_task)
            parent_task_copy.estimated_duration = total_estimate
            self.repository.save(parent_task_copy)

            # Recursively update grandparent if exists
            if parent_task_copy.parent_id:
                self.update_parent_estimated_duration(parent_task_copy.parent_id)

            return parent_task_copy

        return None
