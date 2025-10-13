"""Service for propagating estimated_duration changes to parent tasks."""

import copy

from domain.entities.task import Task
from domain.services.task_eligibility_checker import TaskEligibilityChecker


class EstimatedDurationPropagator:
    """Service for propagating estimated_duration to parent tasks.

    When a child task's estimated_duration changes, this service automatically
    updates the parent task's estimated_duration to be the sum of all children's
    estimated_duration values. This propagation occurs recursively up the
    task hierarchy.
    """

    def __init__(self, repository):
        """Initialize propagator.

        Args:
            repository: Task repository for hierarchy queries and persistence
        """
        self.repository = repository

    def propagate(self, parent_id: int) -> Task | None:
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
                self.propagate(parent_task_copy.parent_id)

            return parent_task_copy

        return None
