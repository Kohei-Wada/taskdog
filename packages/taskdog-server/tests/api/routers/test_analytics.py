"""Tests for analytics router (statistics, optimization, gantt chart)."""

import unittest
from datetime import date, datetime, timedelta

from taskdog_core.domain.entities.task import Task, TaskStatus
from tests.test_base import BaseApiRouterTest


class TestAnalyticsRouter(BaseApiRouterTest):
    """Test cases for analytics router endpoints."""

    def test_get_statistics_with_no_tasks(self):
        """Test getting statistics when no tasks exist."""
        # Act
        response = self.client.get("/api/v1/statistics?period=all")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("completion", data)
        self.assertEqual(data["completion"]["total"], 0)
        self.assertEqual(data["completion"]["completed"], 0)
        self.assertEqual(data["completion"]["completion_rate"], 0.0)

    def test_get_statistics_with_tasks(self):
        """Test getting statistics with tasks in various states."""
        # Arrange - create tasks

        tasks = [
            Task(
                id=1,
                name="Completed Task",
                priority=1,
                status=TaskStatus.COMPLETED,
                actual_start=datetime.now(),
                actual_end=datetime.now(),
            ),
            Task(
                id=2,
                name="In Progress Task",
                priority=2,
                status=TaskStatus.IN_PROGRESS,
                actual_start=datetime.now(),
            ),
            Task(id=3, name="Pending Task", priority=3, status=TaskStatus.PENDING),
            Task(id=4, name="Canceled Task", priority=1, status=TaskStatus.CANCELED),
        ]
        for task in tasks:
            self.repository.save(task)

        # Act
        response = self.client.get("/api/v1/statistics?period=all")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["completion"]["total"], 4)
        self.assertEqual(data["completion"]["completed"], 1)
        self.assertEqual(data["completion"]["in_progress"], 1)
        self.assertEqual(data["completion"]["pending"], 1)
        self.assertEqual(data["completion"]["canceled"], 1)

    def test_get_statistics_invalid_period(self):
        """Test getting statistics with invalid period parameter."""
        # Act
        response = self.client.get("/api/v1/statistics?period=invalid")

        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.json())
        self.assertIn("Period must be one of", response.json()["detail"])

    def test_get_statistics_7d_period(self):
        """Test getting statistics for last 7 days."""
        # Act
        response = self.client.get("/api/v1/statistics?period=7d")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("completion", data)

    def test_get_statistics_30d_period(self):
        """Test getting statistics for last 30 days."""
        # Act
        response = self.client.get("/api/v1/statistics?period=30d")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("completion", data)

    # ===== GET /tags/statistics Tests =====

    def test_get_tag_statistics_with_no_tasks(self):
        """Test getting tag statistics when no tasks exist."""
        # Act
        response = self.client.get("/api/v1/tags/statistics")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total_tags"], 0)
        self.assertEqual(len(data["tags"]), 0)

    def test_get_tag_statistics_with_tasks(self):
        """Test getting tag statistics with tagged tasks."""
        # Arrange - create tasks with tags

        tasks = [
            Task(id=1, name="Task 1", priority=1, tags=["backend", "api"]),
            Task(id=2, name="Task 2", priority=1, tags=["backend", "database"]),
            Task(id=3, name="Task 3", priority=1, tags=["frontend"]),
        ]
        for task in tasks:
            self.repository.save(task)

        # Act
        response = self.client.get("/api/v1/tags/statistics")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # We have 4 unique tags: backend, api, database, frontend
        self.assertEqual(data["total_tags"], 4)
        self.assertEqual(len(data["tags"]), 4)

        # Check tag counts
        tag_names = {tag["tag"] for tag in data["tags"]}
        self.assertIn("backend", tag_names)
        self.assertIn("api", tag_names)
        self.assertIn("frontend", tag_names)
        self.assertIn("database", tag_names)

    # ===== GET /gantt Tests =====

    def test_get_gantt_chart_with_no_tasks(self):
        """Test getting Gantt chart data when no tasks exist."""
        # Act
        response = self.client.get("/api/v1/gantt")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("date_range", data)
        self.assertIn("tasks", data)
        self.assertEqual(len(data["tasks"]), 0)
        self.assertIn("daily_workload", data)
        self.assertIn("holidays", data)

    def test_get_gantt_chart_with_tasks(self):
        """Test getting Gantt chart data with scheduled tasks."""
        # Arrange - create tasks with schedules

        today = date.today()
        tomorrow = today + timedelta(days=1)

        task = Task(
            id=1,
            name="Scheduled Task",
            priority=1,
            planned_start=datetime.combine(today, datetime.min.time()),
            planned_end=datetime.combine(tomorrow, datetime.min.time()),
            estimated_duration=8.0,
            daily_allocations={today: 4.0, tomorrow: 4.0},
        )
        self.repository.save(task)

        # Act
        response = self.client.get("/api/v1/gantt")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["tasks"]), 1)
        self.assertEqual(data["tasks"][0]["name"], "Scheduled Task")
        self.assertIn("daily_allocations", data["tasks"][0])

    def test_get_gantt_chart_with_status_filter(self):
        """Test getting Gantt chart data with status filter."""
        # Arrange - create tasks with different statuses

        tasks = [
            Task(id=1, name="Pending Task", priority=1, status=TaskStatus.PENDING),
            Task(id=2, name="Completed Task", priority=1, status=TaskStatus.COMPLETED),
        ]
        for task in tasks:
            self.repository.save(task)

        # Act
        response = self.client.get("/api/v1/gantt?status=PENDING")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["tasks"]), 1)
        self.assertEqual(data["tasks"][0]["status"], "PENDING")

    def test_get_gantt_chart_with_tag_filter(self):
        """Test getting Gantt chart data with tag filter."""
        # Arrange - create tasks with tags

        tasks = [
            Task(id=1, name="Backend Task", priority=1, tags=["backend"]),
            Task(id=2, name="Frontend Task", priority=1, tags=["frontend"]),
        ]
        for task in tasks:
            self.repository.save(task)

        # Act
        response = self.client.get("/api/v1/gantt?tags=backend")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["tasks"]), 1)

    def test_get_gantt_chart_with_date_range(self):
        """Test getting Gantt chart data with date range filter."""
        # Arrange
        today = date.today()
        start_date = today.isoformat()
        end_date = (today + timedelta(days=7)).isoformat()

        # Act
        response = self.client.get(
            f"/api/v1/gantt?start_date={start_date}&end_date={end_date}"
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("date_range", data)

    def test_get_gantt_chart_include_archived(self):
        """Test getting Gantt chart data including archived tasks."""
        # Arrange - create archived task

        task = Task(id=1, name="Archived Task", priority=1, is_archived=True)
        self.repository.save(task)

        # Act - without all flag
        response1 = self.client.get("/api/v1/gantt")
        # Act - with all flag
        response2 = self.client.get("/api/v1/gantt?all=true")

        # Assert
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(len(response1.json()["tasks"]), 0)  # Archived excluded

        self.assertEqual(response2.status_code, 200)
        self.assertEqual(len(response2.json()["tasks"]), 1)  # Archived included

    def test_get_gantt_chart_with_sorting(self):
        """Test getting Gantt chart data with sorting."""
        # Arrange - create tasks with different deadlines

        today = date.today()
        tasks = [
            Task(
                id=1,
                name="Task A",
                priority=1,
                deadline=datetime.combine(
                    today + timedelta(days=2), datetime.min.time()
                ),
            ),
            Task(
                id=2,
                name="Task B",
                priority=1,
                deadline=datetime.combine(
                    today + timedelta(days=1), datetime.min.time()
                ),
            ),
        ]
        for task in tasks:
            self.repository.save(task)

        # Act
        response = self.client.get("/api/v1/gantt?sort=deadline&reverse=false")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["tasks"]), 2)
        # First task should have earlier deadline
        self.assertEqual(data["tasks"][0]["name"], "Task B")

    # ===== POST /optimize Tests =====

    def test_optimize_schedule_success(self):
        """Test successful schedule optimization."""
        # Arrange - create tasks to optimize

        task = Task(
            id=1,
            name="Task to Optimize",
            priority=1,
            estimated_duration=8.0,
            status=TaskStatus.PENDING,
        )
        self.repository.save(task)

        request_data = {
            "algorithm": "greedy",
            "start_date": datetime.now().isoformat(),
            "max_hours_per_day": 8.0,
            "force_override": False,
        }

        # Act
        response = self.client.post("/api/v1/optimize", json=request_data)

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("summary", data)
        self.assertIn("failures", data)
        self.assertIn("message", data)
        self.assertEqual(data["summary"]["algorithm"], "greedy")

    def test_optimize_schedule_async_mode(self):
        """Test schedule optimization in async mode."""
        # Arrange
        request_data = {
            "algorithm": "greedy",
            "start_date": datetime.now().isoformat(),
            "max_hours_per_day": 8.0,
            "force_override": False,
        }

        # Act
        response = self.client.post(
            "/api/v1/optimize?run_async=true", json=request_data
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("background", data["message"].lower())

    def test_optimize_schedule_with_defaults(self):
        """Test schedule optimization with default parameters."""
        # Arrange - create task

        task = Task(
            id=1,
            name="Task",
            priority=1,
            estimated_duration=4.0,
            status=TaskStatus.PENDING,
        )
        self.repository.save(task)

        request_data = {"algorithm": "greedy"}

        # Act
        response = self.client.post("/api/v1/optimize", json=request_data)

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("summary", data)

    def test_optimize_schedule_with_failures(self):
        """Test schedule optimization with tasks that fail to schedule."""
        # Arrange - create task with impossible constraints

        task = Task(
            id=1,
            name="Impossible Task",
            priority=1,
            estimated_duration=100.0,  # Too many hours
            deadline=datetime.combine(
                date.today() + timedelta(days=1), datetime.min.time()
            ),
            status=TaskStatus.PENDING,
        )
        self.repository.save(task)

        request_data = {
            "algorithm": "greedy",
            "max_hours_per_day": 8.0,
            "force_override": False,
        }

        # Act
        response = self.client.post("/api/v1/optimize", json=request_data)

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(data["summary"]["failed_tasks"], 0)
        self.assertGreater(len(data["failures"]), 0)

    def test_optimize_schedule_force_override(self):
        """Test schedule optimization with force override."""
        # Arrange - create task with existing schedule

        today = date.today()
        task = Task(
            id=1,
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
        self.repository.save(task)

        request_data = {
            "algorithm": "greedy",
            "force_override": True,
            "max_hours_per_day": 8.0,
        }

        # Act
        response = self.client.post("/api/v1/optimize", json=request_data)

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("summary", data)

    # ===== GET /algorithms Tests =====

    def test_list_algorithms(self):
        """Test listing available optimization algorithms."""
        # Act
        response = self.client.get("/api/v1/algorithms")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

        # Check structure of first algorithm
        first_algo = data[0]
        self.assertIn("name", first_algo)
        self.assertIn("display_name", first_algo)
        self.assertIn("description", first_algo)

    def test_list_algorithms_includes_greedy(self):
        """Test that algorithm list includes greedy algorithm."""
        # Act
        response = self.client.get("/api/v1/algorithms")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        algorithm_names = [algo["name"] for algo in data]
        self.assertIn("greedy", algorithm_names)


if __name__ == "__main__":
    unittest.main()
