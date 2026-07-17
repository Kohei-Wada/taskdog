"""E2E: schedule optimization runs against real data via the real server."""

from taskdog_client.taskdog_api_client import TaskdogApiClient


def test_optimize_runs(client: TaskdogApiClient) -> None:
    client.create_task(name="opt a", estimated_duration=2.0)
    client.create_task(name="opt b", estimated_duration=3.0)

    algorithms = client.get_algorithm_metadata()
    assert algorithms, "server should expose at least one algorithm"
    algorithm_key = algorithms[0][0]

    result = client.optimize_schedule(
        algorithm=algorithm_key,
        start_date=None,
        max_hours_per_day=8.0,
    )

    assert result is not None
    assert len(result.successful_tasks) == 2, (
        "Both tasks should be successfully scheduled"
    )
