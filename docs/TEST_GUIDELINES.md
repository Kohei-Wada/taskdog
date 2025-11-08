# Test Guidelines

This document provides guidelines for writing tests in the taskdog project.

## Table of Contents

- [Test Structure](#test-structure)
- [Base Test Classes](#base-test-classes)
- [Test Fixtures and Factories](#test-fixtures-and-factories)
- [Custom Assertions](#custom-assertions)
- [Best Practices](#best-practices)
- [Examples](#examples)

## Test Structure

Tests are organized to mirror the source code structure:

```
packages/
├── taskdog-core/
│   ├── src/taskdog_core/          # Source code
│   └── tests/                      # Tests mirror src structure
│       ├── test_base.py           # Base test classes
│       ├── fixtures.py            # Test fixtures
│       ├── builders.py            # Test builders
│       ├── assertions.py          # Custom assertions
│       ├── domain/
│       ├── application/
│       └── infrastructure/
├── taskdog-server/
│   ├── src/taskdog_server/
│   └── tests/
│       ├── test_base.py           # Server-specific base classes
│       └── api/
└── taskdog-ui/
    ├── src/taskdog/
    └── tests/
        ├── cli/
        └── tui/
```

## Base Test Classes

### When to Use Base Classes

Use base test classes to eliminate setup/teardown duplication. The project provides several base classes:

#### 1. `BaseRepositoryTestCase` (taskdog-core)

**Use when:** Your test needs a SqliteTaskRepository with temporary database.

**What it provides:**
- `self.repository`: SqliteTaskRepository instance
- `self.test_filename`: Path to temporary database file
- Automatic cleanup after each test

**Example:**
```python
from tests.test_base import BaseRepositoryTestCase

class TestCreateTaskUseCase(BaseRepositoryTestCase):
    def setUp(self):
        super().setUp()  # IMPORTANT: Call parent setUp
        self.use_case = CreateTaskUseCase(self.repository)

    def test_creates_task(self):
        # self.repository is ready to use
        result = self.use_case.execute(...)
        self.assertIsNotNone(result.id)
```

**Files affected:** 26+ use case and controller tests

---

#### 2. `BaseApiRouterTestCase` (taskdog-server)

**Use when:** Testing FastAPI router endpoints.

**What it provides:**
- `self.client`: FastAPI TestClient
- `self.repository`: SqliteTaskRepository instance
- `self.config`: Mock config with sensible defaults
- All controllers pre-initialized
- All routers registered
- Helper method: `create_task_in_db(**kwargs)`

**Example:**
```python
from tests.test_base import BaseApiRouterTestCase

class TestTasksRouter(BaseApiRouterTestCase):
    def test_create_task(self):
        # All setup already done
        response = self.client.post("/api/v1/tasks/", json={
            "name": "New Task",
            "priority": 1
        })
        self.assertEqual(response.status_code, 201)
```

**Files affected:** 3 API router test files (~80 lines of setup each)

---

#### 3. Existing Base Classes (Already in Use)

**`BaseStatusChangeUseCaseTest`** - For status change use cases (start, complete, pause, cancel)
- Used by: `test_start_task_use_case.py`, `test_complete_task_use_case.py`, etc.

**`BaseOptimizationStrategyTest`** - For optimization strategy tests
- Used by: All 9 optimization strategy tests

**`BaseBatchCommandTest`** - For CLI batch command tests
- Used by: start, done, pause, cancel, reopen, rm, archive commands

## Test Fixtures and Factories

### Mock Config Factory

**Use when:** You need a mock config object.

```python
from tests.fixtures import create_mock_config

# Use defaults
config = create_mock_config()

# Override specific values
config = create_mock_config(
    default_priority=5,
    max_hours_per_day=10.0,
    country="US"
)

# Use in tests
use_case = CreateTaskUseCase(repository, config)
```

**Available overrides:**
- `default_priority` (default: 3)
- `max_hours_per_day` (default: 8.0)
- `default_algorithm` (default: "greedy")
- `country` (default: None)
- `default_start_hour` (default: 9)
- `default_end_hour` (default: 18)

---

### TaskBuilder

**Use when:** You need to create test tasks with specific attributes.

**Benefits:**
- Fluent API for readability
- Sensible defaults for all fields
- No need to specify every parameter

```python
from tests.builders import TaskBuilder
from taskdog_core.domain.entities.task import TaskStatus

# Simple task with defaults
task = TaskBuilder().build()

# Task with specific attributes
task = (
    TaskBuilder()
    .with_name("Implement feature X")
    .with_priority(1)
    .with_status(TaskStatus.IN_PROGRESS)
    .with_estimated_duration(8.0)
    .build()
)

# Task with dependencies
task = (
    TaskBuilder()
    .with_name("Integration test")
    .with_depends_on([1, 2, 3])
    .with_tags(["urgent", "backend"])
    .build()
)

# Fixed task with schedule
task = (
    TaskBuilder()
    .with_name("Meeting")
    .with_is_fixed(True)
    .with_planned_dates(
        datetime(2025, 1, 15, 10, 0),
        datetime(2025, 1, 15, 11, 0)
    )
    .build()
)
```

**Available methods:**
- `with_id(task_id)`
- `with_name(name)`
- `with_priority(priority)`
- `with_status(status)`
- `with_planned_dates(start, end)`
- `with_deadline(deadline)`
- `with_actual_dates(start, end)`
- `with_estimated_duration(hours)`
- `with_daily_allocations(allocations)`
- `with_is_fixed(is_fixed)`
- `with_depends_on(depends_on)`
- `with_actual_daily_hours(actual_hours)`
- `with_tags(tags)`
- `with_is_archived(is_archived)`

## Custom Assertions

Use custom assertions for domain-specific checks. They provide better error messages and reduce boilerplate.

```python
from tests.assertions import (
    assert_task_has_status,
    assert_task_has_timestamps,
    assert_task_scheduled,
    assert_task_has_allocations,
    assert_total_allocated_hours,
    assert_task_has_dependencies,
    assert_task_has_tags,
    assert_task_is_archived,
    assert_task_is_fixed,
)

# Instead of:
self.assertEqual(task.status, TaskStatus.IN_PROGRESS)

# Use:
assert_task_has_status(task, TaskStatus.IN_PROGRESS)

# Check timestamps
assert_task_has_timestamps(task, actual_start=start_time, actual_end=None)

# Check scheduling
assert_task_scheduled(task, start_date, end_date)

# Check allocations
assert_task_has_allocations(task, {"2025-01-15": 4.0, "2025-01-16": 4.0})
assert_total_allocated_hours(task, 8.0)

# Check relationships
assert_task_has_dependencies(task, [1, 2, 3])
assert_task_has_tags(task, ["urgent", "backend"])

# Check flags
assert_task_is_archived(task)
assert_task_is_fixed(task, False)
```

## Best Practices

### 1. Always Call Parent setUp/tearDown

When extending base classes, always call the parent methods:

```python
class TestMyUseCase(BaseRepositoryTestCase):
    def setUp(self):
        super().setUp()  # REQUIRED
        self.use_case = MyUseCase(self.repository)

    def tearDown(self):
        super().tearDown()  # REQUIRED if you override tearDown
```

### 2. Use Builder Pattern for Complex Test Data

Instead of creating tasks with many parameters:

```python
# ❌ Hard to read
task = Task(
    id=1,
    name="Test",
    priority=3,
    status=TaskStatus.PENDING,
    planned_start=None,
    planned_end=None,
    deadline=None,
    actual_start=None,
    actual_end=None,
    estimated_duration=None,
    daily_allocations=None,
    is_fixed=False,
    depends_on=[],
    actual_daily_hours=None,
    tags=[],
    is_archived=False,
)

# ✅ Clear and concise
task = (
    TaskBuilder()
    .with_name("Test")
    .with_priority(3)
    .build()
)
```

### 3. Use Custom Assertions for Domain Logic

```python
# ❌ Verbose and unclear intent
self.assertEqual(task.status, TaskStatus.COMPLETED)
self.assertIsNotNone(task.actual_start)
self.assertIsNotNone(task.actual_end)

# ✅ Clear intent
assert_task_has_status(task, TaskStatus.COMPLETED)
assert_task_has_timestamps(task, actual_start=start_time, actual_end=end_time)
```

### 4. Isolate Tests with Fresh Database

The `BaseRepositoryTestCase` creates a fresh database for each test method. This ensures test isolation.

```python
class TestMyUseCase(BaseRepositoryTestCase):
    def test_scenario_1(self):
        # Fresh database
        task = TaskBuilder().build()
        self.repository.save(task)
        # ...

    def test_scenario_2(self):
        # Another fresh database (scenario_1's data doesn't exist)
        task = TaskBuilder().build()
        self.repository.save(task)
        # ...
```

### 5. Use Descriptive Test Names

Follow the pattern: `test_<method>_<scenario>_<expected_result>`

```python
def test_execute_with_valid_input_creates_task(self):
    ...

def test_execute_with_invalid_priority_raises_validation_error(self):
    ...

def test_start_when_task_already_in_progress_raises_error(self):
    ...
```

### 6. Favor Dependency Injection Over Patching

```python
# ❌ Excessive patching
@patch('module.Repository')
@patch('module.Config')
def test_something(self, mock_config, mock_repo):
    ...

# ✅ Constructor injection (already provided by base class)
class TestMyUseCase(BaseRepositoryTestCase):
    def setUp(self):
        super().setUp()
        config = create_mock_config()
        self.use_case = MyUseCase(self.repository, config)

    def test_something(self):
        # No patching needed
        ...
```

## Examples

### Example 1: Use Case Test

```python
"""Tests for CreateTaskUseCase"""

from tests.test_base import BaseRepositoryTestCase
from tests.fixtures import create_mock_config
from taskdog_core.application.use_cases.create_task import CreateTaskUseCase
from taskdog_core.application.dto.create_task_input import CreateTaskInput


class TestCreateTaskUseCase(BaseRepositoryTestCase):
    def setUp(self):
        super().setUp()
        config = create_mock_config()
        self.use_case = CreateTaskUseCase(self.repository, config)

    def test_execute_creates_task_with_defaults(self):
        input_dto = CreateTaskInput(name="Test Task")

        result = self.use_case.execute(input_dto)

        self.assertIsNotNone(result.id)
        self.assertEqual(result.name, "Test Task")
        self.assertEqual(result.priority, 3)  # from config default
```

### Example 2: API Router Test

```python
"""Tests for tasks router"""

from tests.test_base import BaseApiRouterTestCase
from taskdog_core.domain.entities.task import TaskStatus


class TestTasksRouter(BaseApiRouterTestCase):
    def test_list_tasks_returns_all_tasks(self):
        # Use helper to create test data
        self.create_task_in_db(name="Task 1", priority=1)
        self.create_task_in_db(name="Task 2", priority=2)

        response = self.client.get("/api/v1/tasks/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["tasks"]), 2)
```

### Example 3: Using TaskBuilder and Custom Assertions

```python
"""Tests demonstrating builders and assertions"""

from datetime import datetime
from tests.test_base import BaseRepositoryTestCase
from tests.builders import TaskBuilder
from tests.assertions import (
    assert_task_has_status,
    assert_task_scheduled,
    assert_total_allocated_hours,
)
from taskdog_core.domain.entities.task import TaskStatus


class TestOptimization(BaseRepositoryTestCase):
    def test_optimizes_task_schedule(self):
        # Create test task with builder
        task = (
            TaskBuilder()
            .with_name("Feature Implementation")
            .with_estimated_duration(16.0)
            .with_deadline(datetime(2025, 2, 1))
            .build()
        )
        self.repository.save(task)

        # Run optimization
        optimizer.optimize()

        # Retrieve and verify
        optimized = self.repository.find_by_id(task.id)
        assert_task_scheduled(
            optimized,
            datetime(2025, 1, 15, 9, 0),
            datetime(2025, 1, 16, 17, 0)
        )
        assert_total_allocated_hours(optimized, 16.0)
```

## Migration Path for Existing Tests

**Current Strategy:** Create infrastructure, don't modify existing tests.

1. ✅ **New tests**: Use base classes from day 1
2. ⏳ **Existing tests**: Gradually migrate when modifying
3. 📝 **Documentation**: This guide serves as reference

**Future migration** (optional):
- When fixing bugs in old tests, migrate to base classes
- When adding test coverage, use new infrastructure
- Consider gradual migration of high-value files first

## Summary

| Tool | Use Case | Files Affected | Benefit |
|------|----------|----------------|---------|
| `BaseRepositoryTestCase` | Use case & controller tests | 26+ files | Eliminates ~400 LOC duplication |
| `BaseApiRouterTestCase` | API router tests | 3 files | Eliminates ~240 LOC duplication |
| `create_mock_config()` | Mock config setup | 8+ files | Standardizes config mocking |
| `TaskBuilder` | Creating test tasks | Many files | Improves readability, reduces boilerplate |
| Custom assertions | Domain-specific checks | All tests | Better error messages, clearer intent |

**Key Principle:** Make tests easy to read and write. Reduce duplication. Favor clarity over brevity.
