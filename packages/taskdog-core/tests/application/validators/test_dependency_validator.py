"""Tests for DependencyValidator."""

from unittest.mock import Mock

import pytest

from taskdog_core.application.validators.dependency_validator import DependencyValidator
from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.exceptions.task_exceptions import DependencyNotMetError


class TestDependencyValidator:
    """Test cases for DependencyValidator."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize mock repository for each test."""
        self.mock_repository = Mock()

    @pytest.mark.parametrize(
        "scenario_name,task_id,depends_on,dep_configs,should_pass,expected_unmet_deps",
        [
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
        ],
        ids=[
            "no_dependencies",
            "all_completed_single",
            "all_completed_multiple",
            "pending_dependency",
            "in_progress_dependency",
            "canceled_dependency",
            "missing_dependency",
            "mixed_completed_and_pending",
            "all_unmet_mixed_statuses",
        ],
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
        # No dependencies case - no need to mock

        if should_pass:
            # Should not raise
            DependencyValidator.validate_dependencies_met(task, self.mock_repository)
        else:
            # Should raise DependencyNotMetError
            with pytest.raises(DependencyNotMetError) as exc_info:
                DependencyValidator.validate_dependencies_met(
                    task, self.mock_repository
                )

            assert exc_info.value.task_id == task_id
            for unmet_dep_id in expected_unmet_deps:
                assert unmet_dep_id in exc_info.value.unmet_dependencies

            # For mixed cases, verify met dependencies are NOT in the list
            if "mixed" in scenario_name:
                for dep_id, status in dep_configs.items():
                    if status == TaskStatus.COMPLETED:
                        assert dep_id not in exc_info.value.unmet_dependencies

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
