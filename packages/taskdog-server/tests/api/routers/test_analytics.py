"""Tests for analytics router (statistics, optimization, gantt chart)."""

from datetime import date, datetime, timedelta

import pytest

from taskdog_core.domain.entities.task import TaskStatus


class TestAnalyticsRouter:
    """Test cases for analytics router endpoints."""

    def test_get_statistics_with_no_tasks(self, client):
        """Test getting statistics when no tasks exist."""
        # Act
        response = client.get("/api/v1/statistics?period=all")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "completion" in data
        assert data["completion"]["total"] == 0
        assert data["completion"]["completed"] == 0
        assert data["completion"]["completion_rate"] == 0.0

    def test_get_statistics_with_tasks(self, client, repository, task_factory):
        """Test getting statistics with tasks in various states."""
        # Arrange - create tasks
        task_factory.create(name="Completed Task", priority=1)
        completed_task = repository.get_all()[-1]
        completed_task.status = TaskStatus.COMPLETED
        completed_task.actual_start = datetime.now()
        completed_task.actual_end = datetime.now()
        repository.save(completed_task)

        task_factory.create(name="In Progress Task", priority=2)
        in_progress_task = repository.get_all()[-1]
        in_progress_task.status = TaskStatus.IN_PROGRESS
        in_progress_task.actual_start = datetime.now()
        repository.save(in_progress_task)

        task_factory.create(name="Pending Task", priority=3, status=TaskStatus.PENDING)

        task_factory.create(name="Canceled Task", priority=1)
        canceled_task = repository.get_all()[-1]
        canceled_task.status = TaskStatus.CANCELED
        repository.save(canceled_task)

        # Act
        response = client.get("/api/v1/statistics?period=all")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["completion"]["total"] == 4
        assert data["completion"]["completed"] == 1
        assert data["completion"]["in_progress"] == 1
        assert data["completion"]["pending"] == 1
        assert data["completion"]["canceled"] == 1

    def test_get_statistics_invalid_period(self, client):
        """Test getting statistics with invalid period parameter."""
        # Act
        response = client.get("/api/v1/statistics?period=invalid")

        # Assert
        assert response.status_code == 400
        assert "detail" in response.json()
        assert "Period must be one of" in response.json()["detail"]

    @pytest.mark.parametrize("period", ["7d", "30d"])
    def test_get_statistics_valid_period(self, client, period):
        """Test getting statistics for valid time periods."""
        response = client.get(f"/api/v1/statistics?period={period}")
        assert response.status_code == 200
        assert "completion" in response.json()

    # ===== GET /tags/statistics Tests =====

    def test_get_tag_statistics_with_no_tasks(self, client):
        """Test getting tag statistics when no tasks exist."""
        # Act
        response = client.get("/api/v1/tags/statistics")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_tags"] == 0
        assert len(data["tags"]) == 0

    def test_get_tag_statistics_with_tasks(self, client, task_factory):
        """Test getting tag statistics with tagged tasks."""
        # Arrange - create tasks with tags
        task_factory.create(name="Task 1", priority=1, tags=["backend", "api"])
        task_factory.create(name="Task 2", priority=1, tags=["backend", "database"])
        task_factory.create(name="Task 3", priority=1, tags=["frontend"])

        # Act
        response = client.get("/api/v1/tags/statistics")

        # Assert
        assert response.status_code == 200
        data = response.json()
        # We have 4 unique tags: backend, api, database, frontend
        assert data["total_tags"] == 4
        assert len(data["tags"]) == 4

        # Check tag counts
        tag_names = {tag["tag"] for tag in data["tags"]}
        assert "backend" in tag_names
        assert "api" in tag_names
        assert "frontend" in tag_names
        assert "database" in tag_names

    # ===== GET /gantt Tests =====

    def test_get_gantt_chart_with_no_tasks(self, client):
        """Test getting Gantt chart data when no tasks exist."""
        # Act
        response = client.get("/api/v1/gantt")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "date_range" in data
        assert "tasks" in data
        assert len(data["tasks"]) == 0
        assert "daily_workload" in data
        assert "holidays" in data

    def test_get_gantt_chart_with_tasks(self, client, task_factory):
        """Test getting Gantt chart data with scheduled tasks."""
        # Arrange - create tasks with schedules
        today = date.today()
        tomorrow = today + timedelta(days=1)

        task_factory.create(
            name="Scheduled Task",
            priority=1,
            planned_start=datetime.combine(today, datetime.min.time()),
            planned_end=datetime.combine(tomorrow, datetime.min.time()),
            estimated_duration=8.0,
            daily_allocations={today: 4.0, tomorrow: 4.0},
        )

        # Act
        response = client.get("/api/v1/gantt")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["name"] == "Scheduled Task"
        assert "daily_allocations" in data["tasks"][0]

    def test_get_gantt_chart_with_status_filter(self, client, repository, task_factory):
        """Test getting Gantt chart data with status filter."""
        # Arrange - create tasks with different statuses
        task_factory.create(name="Pending Task", priority=1, status=TaskStatus.PENDING)
        task_factory.create(name="Completed Task", priority=1)
        completed_task = repository.get_all()[-1]
        completed_task.status = TaskStatus.COMPLETED
        repository.save(completed_task)

        # Act
        response = client.get("/api/v1/gantt?status=PENDING")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["status"] == "PENDING"

    def test_get_gantt_chart_with_tag_filter(self, client, task_factory):
        """Test getting Gantt chart data with tag filter."""
        # Arrange - create tasks with tags
        task_factory.create(name="Backend Task", priority=1, tags=["backend"])
        task_factory.create(name="Frontend Task", priority=1, tags=["frontend"])

        # Act
        response = client.get("/api/v1/gantt?tags=backend")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 1

    def test_get_gantt_chart_with_date_range(self, client):
        """Test getting Gantt chart data with date range filter."""
        # Arrange
        today = date.today()
        start_date = today.isoformat()
        end_date = (today + timedelta(days=7)).isoformat()

        # Act
        response = client.get(
            f"/api/v1/gantt?start_date={start_date}&end_date={end_date}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "date_range" in data

    def test_get_gantt_chart_include_archived(self, client, task_factory):
        """Test getting Gantt chart data including archived tasks."""
        # Arrange - create archived task
        task_factory.create(name="Archived Task", priority=1, is_archived=True)

        # Act - without all flag
        response1 = client.get("/api/v1/gantt")
        # Act - with all flag
        response2 = client.get("/api/v1/gantt?all=true")

        # Assert
        assert response1.status_code == 200
        assert len(response1.json()["tasks"]) == 0  # Archived excluded

        assert response2.status_code == 200
        assert len(response2.json()["tasks"]) == 1  # Archived included

    def test_get_gantt_chart_with_sorting(self, client, task_factory):
        """Test getting Gantt chart data with sorting."""
        # Arrange - create tasks with different deadlines
        today = date.today()
        task_factory.create(
            name="Task A",
            priority=1,
            deadline=datetime.combine(today + timedelta(days=2), datetime.min.time()),
        )
        task_factory.create(
            name="Task B",
            priority=1,
            deadline=datetime.combine(today + timedelta(days=1), datetime.min.time()),
        )

        # Act
        response = client.get("/api/v1/gantt?sort=deadline&reverse=false")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 2
        # First task should have earlier deadline
        assert data["tasks"][0]["name"] == "Task B"

    # ===== POST /optimize Tests =====

    def test_optimize_schedule_success(self, client, task_factory):
        """Test successful schedule optimization."""
        # Arrange - create tasks to optimize
        task_factory.create(
            name="Task to Optimize",
            priority=1,
            estimated_duration=8.0,
            status=TaskStatus.PENDING,
        )

        request_data = {
            "algorithm": "greedy",
            "start_date": datetime.now().isoformat(),
            "max_hours_per_day": 8.0,
            "force_override": False,
        }

        # Act
        response = client.post("/api/v1/optimize", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "failures" in data
        assert "message" in data
        assert data["summary"]["algorithm"] == "greedy"

    def test_optimize_schedule_with_required_fields(self, client, task_factory):
        """Test schedule optimization with required parameters."""
        # Arrange - create task
        task_factory.create(
            name="Task",
            priority=1,
            estimated_duration=4.0,
            status=TaskStatus.PENDING,
        )

        request_data = {"algorithm": "greedy", "max_hours_per_day": 6.0}

        # Act
        response = client.post("/api/v1/optimize", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data

    def test_optimize_schedule_with_failures(self, client, task_factory):
        """Test schedule optimization with tasks that fail to schedule."""
        # Arrange - create task with impossible constraints
        task_factory.create(
            name="Impossible Task",
            priority=1,
            estimated_duration=100.0,  # Too many hours
            deadline=datetime.combine(
                date.today() + timedelta(days=1), datetime.min.time()
            ),
            status=TaskStatus.PENDING,
        )

        request_data = {
            "algorithm": "greedy",
            "max_hours_per_day": 8.0,
            "force_override": False,
        }

        # Act
        response = client.post("/api/v1/optimize", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["summary"]["failed_tasks"] > 0
        assert len(data["failures"]) > 0

    def test_optimize_schedule_force_override(self, client, task_factory):
        """Test schedule optimization with force override."""
        # Arrange - create task with existing schedule
        today = date.today()
        task_factory.create(
            name="Scheduled Task",
            priority=1,
            estimated_duration=8.0,
            planned_start=datetime.combine(today, datetime.min.time()),
            planned_end=datetime.combine(
                today + timedelta(days=1), datetime.min.time()
            ),
            daily_allocations={today: 8.0},
            is_fixed=False,
            status=TaskStatus.PENDING,
        )

        request_data = {
            "algorithm": "greedy",
            "force_override": True,
            "max_hours_per_day": 8.0,
        }

        # Act
        response = client.post("/api/v1/optimize", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data

    # ===== GET /algorithms Tests =====

    def test_list_algorithms(self, client):
        """Test listing available optimization algorithms."""
        # Act
        response = client.get("/api/v1/algorithms")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Check structure of first algorithm
        first_algo = data[0]
        assert "name" in first_algo
        assert "display_name" in first_algo
        assert "description" in first_algo

    def test_list_algorithms_includes_greedy(self, client):
        """Test that algorithm list includes greedy algorithm."""
        # Act
        response = client.get("/api/v1/algorithms")

        # Assert
        assert response.status_code == 200
        data = response.json()
        algorithm_names = [algo["name"] for algo in data]
        assert "greedy" in algorithm_names

    @pytest.mark.parametrize(
        "include_all_days", [True, False], ids=["with_weekends", "weekdays_only"]
    )
    def test_optimize_schedule_include_all_days(
        self, client, task_factory, include_all_days
    ):
        """Test schedule optimization with and without include_all_days flag."""
        task_factory.create(
            name="Task",
            priority=1,
            estimated_duration=10.0,
            status=TaskStatus.PENDING,
        )
        request_data = {
            "algorithm": "greedy",
            "start_date": datetime(2025, 10, 17, 9, 0, 0).isoformat(),
            "max_hours_per_day": 6.0,
            "force_override": False,
            "include_all_days": include_all_days,
        }
        response = client.post("/api/v1/optimize", json=request_data)
        assert response.status_code == 200
        assert response.json()["summary"]["scheduled_tasks"] == 1
