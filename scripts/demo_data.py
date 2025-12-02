#!/usr/bin/env python3
"""Demo data script for Taskdog - creates sample tasks via REST API.

This script creates ~50 sample tasks with realistic deadlines, estimates,
tags, dependencies, and notes. It uses the REST API directly for better
performance compared to CLI commands.

Projects included:
- Web Application Development (15 tasks)
- Bug Fixes & Improvements (2 tasks)
- Documentation & Maintenance (1 task)
- Long-term Projects (4 tasks)
- Weekend Fixed Tasks (3 tasks)
- Mobile App Development (8 tasks)
- Data Analytics Platform (7 tasks)
- DevOps & Infrastructure (5 tasks)
- Learning & Skill Development (5 tasks)

Usage:
    python demo_data.py [--host HOST] [--port PORT] [--no-confirm] [--workers N]
    python demo_data.py [--api-url URL] [--no-confirm] [--workers N]

Requirements:
    - taskdog-server must be running (default: http://127.0.0.1:8000)
    - Python 3.9+ (uses standard library only)
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Terminal colors
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
NC = "\033[0m"  # No Color

SCRIPT_DIR = Path(__file__).parent
DATA_FILE = SCRIPT_DIR / "demo_data.json"


class TaskdogAPIClient:
    """REST API client for Taskdog server using urllib."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/api/v1"

    def _request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Make HTTP request to API."""
        url = f"{self.api_url}{endpoint}"
        headers = {"Content-Type": "application/json"}

        body = json.dumps(data).encode("utf-8") if data else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status == 204:
                    return None
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            raise RuntimeError(f"API error {e.code}: {error_body}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"Connection error: {e.reason}") from e

    def health_check(self) -> bool:
        """Check if server is running."""
        try:
            req = urllib.request.Request(f"{self.base_url}/health", method="GET")
            with urllib.request.urlopen(req, timeout=5):
                return True
        except (urllib.error.URLError, urllib.error.HTTPError):
            return False

    def create_task(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new task."""
        result = self._request("POST", "/tasks", data)
        if result is None:
            raise RuntimeError("Unexpected empty response from create_task")
        return result

    def add_dependency(self, task_id: int, depends_on_id: int) -> None:
        """Add dependency between tasks."""
        self._request(
            "POST",
            f"/tasks/{task_id}/dependencies",
            {"depends_on_id": depends_on_id},
        )

    def update_notes(self, task_id: int, content: str) -> None:
        """Update task notes."""
        self._request("PUT", f"/tasks/{task_id}/notes", {"content": content})

    def update_task(self, task_id: int, data: dict[str, Any]) -> None:
        """Update task fields."""
        self._request("PATCH", f"/tasks/{task_id}", data)

    def start_task(self, task_id: int) -> None:
        """Start a task."""
        self._request("POST", f"/tasks/{task_id}/start", {})

    def complete_task(self, task_id: int) -> None:
        """Complete a task."""
        self._request("POST", f"/tasks/{task_id}/complete", {})

    def optimize_schedule(
        self,
        algorithm: str = "greedy",
        start_date: str | None = None,
        max_hours_per_day: float = 8.0,
    ) -> dict[str, Any]:
        """Run schedule optimization."""
        data: dict[str, Any] = {
            "algorithm": algorithm,
            "max_hours_per_day": max_hours_per_day,
            "force_override": True,
        }
        if start_date:
            data["start_date"] = start_date
        result = self._request("POST", "/optimize", data)
        if result is None:
            raise RuntimeError("Unexpected empty response from optimize_schedule")
        return result


class DemoDataLoader:
    """Load demo data from JSON and resolve relative dates."""

    def __init__(self, data_file: Path = DATA_FILE):
        self.data_file = data_file
        self.today = datetime.now().date()

    def load(self) -> dict[str, Any]:
        """Load and parse JSON data file."""
        with open(self.data_file, encoding="utf-8") as f:
            return json.load(f)

    def resolve_date(self, days: int) -> str:
        """Resolve relative days to ISO date string."""
        target = self.today + timedelta(days=days)
        return target.isoformat()

    def resolve_weekend(
        self, offset: int = 0, day: str = "saturday"
    ) -> tuple[str, str]:
        """Resolve weekend dates.

        Args:
            offset: 0 = next weekend, 1 = following weekend
            day: 'saturday' or 'sunday'

        Returns:
            Tuple of (start_date, end_date) for schedule
        """
        dow = self.today.weekday()  # 0=Monday, 6=Sunday

        # Calculate days until Saturday (5) or Sunday (6)
        target_dow = 6 if day == "sunday" else 5

        days_until = (target_dow - dow) % 7
        if days_until == 0 and dow != target_dow:
            days_until = 7

        days_until += offset * 7

        target = self.today + timedelta(days=days_until)
        date_str = target.isoformat()
        return date_str, date_str

    def resolve_weekend_range(self, offset: int = 0) -> tuple[str, str]:
        """Resolve weekend date range (Saturday to Sunday).

        Args:
            offset: 0 = next weekend, 1 = following weekend

        Returns:
            Tuple of (saturday, sunday) date strings
        """
        dow = self.today.weekday()
        days_until_sat = (5 - dow) % 7
        if days_until_sat == 0 and dow != 5:
            days_until_sat = 7
        days_until_sat += offset * 7

        saturday = self.today + timedelta(days=days_until_sat)
        sunday = saturday + timedelta(days=1)
        return saturday.isoformat(), sunday.isoformat()


class DemoDataCreator:
    """Create demo data using the API."""

    def __init__(
        self,
        client: TaskdogAPIClient,
        loader: DemoDataLoader,
        max_workers: int = 5,
    ):
        self.client = client
        self.loader = loader
        self.max_workers = max_workers
        self.task_id_map: dict[str, int] = {}  # T1 -> actual_id

    def run(self) -> None:
        """Execute the demo data creation."""
        data = self.loader.load()

        # Phase 1: Create all tasks (parallel)
        print(f"{BLUE}Creating tasks...{NC}")
        all_tasks = []
        for project in data["projects"]:
            print(f"{BLUE}[{project['name']}]{NC}")
            for task in project["tasks"]:
                all_tasks.append(task)

        self._create_tasks_parallel(all_tasks)

        # Phase 2: Add dependencies (sequential, after all tasks created)
        print(f"\n{BLUE}Adding dependencies...{NC}")
        self._add_dependencies(all_tasks)

        # Phase 3: Update notes (parallel)
        print(f"\n{BLUE}Setting notes...{NC}")
        self._update_notes_parallel(all_tasks)

        # Phase 4: Set schedules for fixed tasks (parallel)
        print(f"\n{BLUE}Setting schedules for fixed tasks...{NC}")
        self._set_schedules_parallel(all_tasks)

        # Phase 5: Simulate progress
        print(f"\n{BLUE}Simulating progress...{NC}")
        progress = data.get("progress", {})
        self._simulate_progress(progress)

        # Phase 6: Run optimization
        print(f"\n{BLUE}Running schedule optimization...{NC}")
        opt_config = data.get("optimization", {})
        self._run_optimization(opt_config)

        # Summary
        self._print_summary(data)

    def _create_tasks_parallel(self, tasks: list[dict[str, Any]]) -> None:
        """Create tasks in parallel."""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._create_single_task, task): task for task in tasks
            }
            for future in as_completed(futures):
                task = futures[future]
                try:
                    task_id, name = future.result()
                    print(f"  {GREEN}✓{NC} {name} (ID: {task_id})")
                except Exception as e:
                    print(f"  {RED}✗{NC} {task['name']}: {e}")

    def _create_single_task(self, task: dict[str, Any]) -> tuple[int, str]:
        """Create a single task and return (id, name)."""
        # Build request data
        req_data: dict[str, Any] = {
            "name": task["name"],
            "priority": task.get("priority"),
            "tags": task.get("tags", []),
            "estimated_duration": task.get("estimate"),
            "is_fixed": task.get("is_fixed", False),
        }

        # Resolve deadline
        if "deadline_days" in task:
            deadline = self.loader.resolve_date(task["deadline_days"])
            req_data["deadline"] = f"{deadline}T18:00:00"
        elif task.get("weekend"):
            offset = task.get("weekend_offset", 0)
            day = task.get("weekend_day", "sunday")
            deadline, _ = self.loader.resolve_weekend(offset, day)
            req_data["deadline"] = f"{deadline}T18:00:00"

        # Create task
        result = self.client.create_task(req_data)
        actual_id = result["id"]

        # Store mapping
        self.task_id_map[task["id"]] = actual_id

        return actual_id, task["name"]

    def _add_dependencies(self, tasks: list[dict[str, Any]]) -> None:
        """Add dependencies between tasks."""
        for task in tasks:
            if "depends_on" not in task:
                continue

            task_id = self.task_id_map.get(task["id"])
            if not task_id:
                continue

            for dep_ref in task["depends_on"]:
                dep_id = self.task_id_map.get(dep_ref)
                if not dep_id:
                    print(f"  {YELLOW}⚠{NC} Skipping dependency: {dep_ref} not found")
                    continue

                try:
                    self.client.add_dependency(task_id, dep_id)
                    print(f"  {GREEN}✓{NC} {task['id']} depends on {dep_ref}")
                except Exception as e:
                    print(f"  {RED}✗{NC} {task['id']} -> {dep_ref}: {e}")

    def _update_notes_parallel(self, tasks: list[dict[str, Any]]) -> None:
        """Update notes in parallel."""
        tasks_with_notes = [t for t in tasks if t.get("note")]

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(
                    self._update_single_note,
                    self.task_id_map[task["id"]],
                    task["note"],
                ): task
                for task in tasks_with_notes
                if task["id"] in self.task_id_map
            }
            for future in as_completed(futures):
                task = futures[future]
                try:
                    future.result()
                except Exception as e:
                    print(f"  {RED}✗{NC} Note for {task['id']}: {e}")

        print(f"  {GREEN}✓{NC} Updated {len(tasks_with_notes)} notes")

    def _update_single_note(self, task_id: int, content: str) -> None:
        """Update note for a single task."""
        self.client.update_notes(task_id, content)

    def _set_schedules_parallel(self, tasks: list[dict[str, Any]]) -> None:
        """Set schedules for fixed tasks."""
        fixed_tasks = [t for t in tasks if t.get("is_fixed") and t.get("weekend")]

        if not fixed_tasks:
            print(f"  {YELLOW}No fixed weekend tasks to schedule{NC}")
            return

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._set_single_schedule, task): task
                for task in fixed_tasks
                if task["id"] in self.task_id_map
            }
            for future in as_completed(futures):
                task = futures[future]
                try:
                    future.result()
                    print(f"  {GREEN}✓{NC} Scheduled: {task['name']}")
                except Exception as e:
                    print(f"  {RED}✗{NC} Schedule for {task['id']}: {e}")

    def _set_single_schedule(self, task: dict[str, Any]) -> None:
        """Set schedule for a single fixed task."""
        task_id = self.task_id_map[task["id"]]
        offset = task.get("weekend_offset", 0)

        # Determine schedule dates
        if task.get("weekend_day") == "sunday":
            # Sunday only
            _, sunday = self.loader.resolve_weekend_range(offset)
            start = end = sunday
        else:
            # Full weekend or Saturday
            start, end = self.loader.resolve_weekend_range(offset)

        self.client.update_task(
            task_id,
            {
                "planned_start": f"{start}T09:00:00",
                "planned_end": f"{end}T18:00:00",
            },
        )

    def _simulate_progress(self, progress: dict[str, list[str]]) -> None:
        """Simulate task progress (start/complete some tasks)."""
        completed = progress.get("completed", [])
        in_progress = progress.get("in_progress", [])

        # Complete tasks (must start first)
        for ref in completed:
            task_id = self.task_id_map.get(ref)
            if not task_id:
                continue
            try:
                self.client.start_task(task_id)
                self.client.complete_task(task_id)
                print(f"  {GREEN}✓{NC} Completed: {ref}")
            except Exception as e:
                print(f"  {RED}✗{NC} Complete {ref}: {e}")

        # Start tasks
        for ref in in_progress:
            task_id = self.task_id_map.get(ref)
            if not task_id:
                continue
            try:
                self.client.start_task(task_id)
                print(f"  {BLUE}⚙{NC} In Progress: {ref}")
            except Exception as e:
                print(f"  {RED}✗{NC} Start {ref}: {e}")

    def _run_optimization(self, config: dict[str, Any]) -> None:
        """Run schedule optimization."""
        tomorrow = (self.loader.today + timedelta(days=1)).isoformat()

        try:
            result = self.client.optimize_schedule(
                algorithm=config.get("algorithm", "greedy"),
                start_date=f"{tomorrow}T09:00:00",
                max_hours_per_day=config.get("max_hours_per_day", 8.0),
            )
            summary = result.get("summary", {})
            print(f"  {GREEN}✓{NC} Optimization completed")
            print(f"    Algorithm: {summary.get('algorithm', 'N/A')}")
            print(f"    Scheduled: {summary.get('scheduled_tasks', 0)} tasks")
            print(f"    Total hours: {summary.get('total_hours', 0):.1f}h")
        except Exception as e:
            print(f"  {RED}✗{NC} Optimization failed: {e}")

    def _print_summary(self, data: dict[str, Any]) -> None:
        """Print final summary."""
        total_tasks = sum(len(project["tasks"]) for project in data["projects"])
        completed = len(data.get("progress", {}).get("completed", []))
        in_progress = len(data.get("progress", {}).get("in_progress", []))
        pending = total_tasks - completed - in_progress

        print(f"\n{BLUE}{'═' * 55}{NC}")
        print(f"{GREEN}  Demo data created successfully!{NC}")
        print(f"{BLUE}{'═' * 55}{NC}")
        print()
        print("Summary:")
        print(f"  • {total_tasks} tasks created")
        print(f"  • {completed} completed tasks")
        print(f"  • {in_progress} in-progress tasks")
        print(f"  • {pending} pending tasks")
        print()
        print(f"{BLUE}Useful commands:{NC}")
        print("  taskdog table          - View all tasks")
        print("  taskdog gantt          - View Gantt chart")
        print("  taskdog today          - View today's tasks")
        print("  taskdog show <ID>      - View task details with notes")
        print("  taskdog optimize       - Auto-schedule tasks")
        print("  taskdog tui            - Open interactive TUI")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create demo data for Taskdog via REST API"
    )
    parser.add_argument(
        "--api-url",
        default=None,
        help="Taskdog API server URL (overrides --host and --port)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="API server host (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=8000,
        help="API server port (default: 8000)",
    )
    parser.add_argument(
        "--no-confirm",
        "-y",
        action="store_true",
        help="Skip confirmation prompt",
    )
    parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=5,
        help="Number of parallel workers (default: 5)",
    )
    args = parser.parse_args()

    # Check data file exists
    if not DATA_FILE.exists():
        print(f"{RED}Error: Data file not found: {DATA_FILE}{NC}")
        return 1

    # Determine API URL
    api_url = args.api_url or f"http://{args.host}:{args.port}"

    # Initialize client
    client = TaskdogAPIClient(api_url)

    # Check server health
    if not client.health_check():
        print(f"{RED}Error: taskdog-server is not running at {api_url}{NC}")
        print("Please start the server with: taskdog-server")
        print("Or: systemctl --user start taskdog-server")
        return 1

    # Print banner
    print(f"{BLUE}{'═' * 55}{NC}")
    print(f"{BLUE}  Taskdog Demo Data Script{NC}")
    print(f"{BLUE}{'═' * 55}{NC}")
    print()
    print("This will create ~50 sample tasks with:")
    print("  • Realistic deadlines (from tomorrow to 3 months ahead)")
    print("  • Various estimates (2-30 hours)")
    print("  • Various tags (work, personal, urgent, etc.)")
    print("  • Task dependencies")
    print("  • Detailed notes with context and actionable items")
    print("  • Some tasks already started/completed")
    print()
    print(f"{YELLOW}Warning: This will add tasks to your current database{NC}")
    print()

    # Confirm
    if not args.no_confirm:
        response = input("Continue? (y/N) ").strip().lower()
        if response not in ("y", "yes"):
            print("Cancelled.")
            return 0

    print()

    # Create demo data
    loader = DemoDataLoader()
    creator = DemoDataCreator(client, loader, max_workers=args.workers)

    try:
        creator.run()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Interrupted.{NC}")
        return 130
    except Exception as e:
        print(f"{RED}Error: {e}{NC}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
