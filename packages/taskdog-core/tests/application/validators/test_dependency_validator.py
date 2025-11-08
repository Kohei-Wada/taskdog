"""Tests for DependencyValidator."""

import unittest
from unittest.mock import Mock

from parameterized import parameterized

from taskdog_core.application.validators.dependency_validator import DependencyValidator
from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.exceptions.task_exceptions import DependencyNotMetError


class TestDependencyValidator(unittest.TestCase):
    """Test cases for DependencyValidator."""

    def setUp(self):
        """Initialize mock repository for each test."""
        self.mock_repository = Mock()

    @parameterized.expand(
        [
            # (scenario_name, task_id, depends_on, dep_configs, should_pass, expected_unmet_deps)
            # dep_configs format: {dep_id: status} or "missing" for empty dict
            # Valid cases
            ("no_dependencies", 1, [], {}, True, None),
            ("all_completed_single", 2, [1], {1: TaskStatus.COMPLETED}, True, None),
            (
                "all_completed_multiple",
                3,
                [1, 2],
                {1: TaskStatus.COMPLETED, 2: TaskStatus.COMPLETED},
                True,
                None,
            ),
            # Invalid cases - single dependency
            ("pending_dependency", 2, [1], {1: TaskStatus.PENDING}, False, [1]),
            ("in_progress_dependency", 2, [1], {1: TaskStatus.IN_PROGRESS}, False, [1]),
            ("canceled_dependency", 2, [1], {1: TaskStatus.CANCELED}, False, [1]),
            ("missing_dependency", 2, [999], "missing", False, [999]),
            # Invalid cases - mixed dependencies
            (
                "mixed_completed_and_pending",
                3,
                [1, 2],
                {1: TaskStatus.COMPLETED, 2: TaskStatus.PENDING},
                False,
                [2],
            ),
            (
                "all_unmet_mixed_statuses",
                4,
                [1, 2, 3],
                {
                    1: TaskStatus.PENDING,
                    2: TaskStatus.IN_PROGRESS,
                    3: TaskStatus.CANCELED,
                },
                False,
                [1, 2, 3],
            ),
        ]
    )
    def test_dependency_validation_scenarios(
        self,
        scenario_name,
        task_id,
        depends_on,
        dep_configs,
        should_pass,
        expected_unmet_deps,
    ):
        """Test validation of dependencies with various scenarios."""
        task = Task(
            id=task_id,
            name="Test",
            status=TaskStatus.PENDING,
            priority=1,
            depends_on=depends_on,
        )

        # Build mock repository response
        if dep_configs == "missing":
            self.mock_repository.get_by_ids.return_value = {}
        elif dep_configs:
            deps_dict = {
                dep_id: Task(id=dep_id, name=f"Dep {dep_id}", status=status, priority=1)
                for dep_id, status in dep_configs.items()
            }
            self.mock_repository.get_by_ids.return_value = deps_dict
        else:
            # No dependencies case - no need to mock
            pass

        if should_pass:
            # Should not raise
            DependencyValidator.validate_dependencies_met(task, self.mock_repository)
        else:
            # Should raise DependencyNotMetError
            with self.assertRaises(DependencyNotMetError) as context:
                DependencyValidator.validate_dependencies_met(
                    task, self.mock_repository
                )

            self.assertEqual(context.exception.task_id, task_id)
            for unmet_dep_id in expected_unmet_deps:
                self.assertIn(unmet_dep_id, context.exception.unmet_dependencies)

            # For mixed cases, verify met dependencies are NOT in the list
            if "mixed" in scenario_name:
                for dep_id, status in dep_configs.items():
                    if status == TaskStatus.COMPLETED:
                        self.assertNotIn(dep_id, context.exception.unmet_dependencies)

    def test_validate_dependencies_uses_get_by_ids(self):
        """Test that validator uses get_by_ids() for batch fetching."""
        task = Task(
            id=3, name="Test", status=TaskStatus.PENDING, priority=1, depends_on=[1, 2]
        )

        # Mock repository to return completed dependencies
        dep1 = Task(id=1, name="Dep 1", status=TaskStatus.COMPLETED, priority=1)
        dep2 = Task(id=2, name="Dep 2", status=TaskStatus.COMPLETED, priority=1)
        self.mock_repository.get_by_ids.return_value = {1: dep1, 2: dep2}

        # Validate dependencies
        DependencyValidator.validate_dependencies_met(task, self.mock_repository)

        # Verify get_by_ids was called once with all dependency IDs
        self.mock_repository.get_by_ids.assert_called_once_with([1, 2])


if __name__ == "__main__":
    unittest.main()
