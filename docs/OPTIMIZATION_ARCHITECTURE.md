# Optimization Architecture

This document describes the architecture of taskdog's task scheduling optimization system.

## Table of Contents

1. [Overview](#overview)
2. [Architecture Patterns](#architecture-patterns)
3. [Core Components](#core-components)
4. [Optimization Strategies](#optimization-strategies)
5. [Data Flow](#data-flow)
6. [Helper Methods](#helper-methods)
7. [Extension Guide](#extension-guide)
8. [Recent Refactorings](#recent-refactorings)

## Overview

The optimization system schedules tasks by allocating work hours across calendar days while respecting constraints like deadlines, work hour limits, and dependencies.

### Design Goals

- **Flexible algorithms**: Support multiple scheduling strategies with different trade-offs
- **Clean abstraction**: Template Method pattern eliminates code duplication
- **Extensible**: Easy to add new strategies without modifying existing code
- **Testable**: Each strategy can be tested independently

### Key Components

- **OptimizationStrategy** - Abstract base class (Template Method pattern)
- **AllocationContext** - State container for optimization parameters
- **StrategyFactory** - Creates strategy instances by name
- **OptimizeScheduleUseCase** - Entry point orchestrating the optimization

## Architecture Patterns

### Template Method Pattern

The `OptimizationStrategy` base class defines the common workflow while allowing strategies to customize specific steps:

```python
class OptimizationStrategy(ABC):
    def optimize_tasks(self, ...):
        # Template method defining the workflow
        context = AllocationContext.create(...)  # 1. Initialize context
        sorted_tasks = self._sort_schedulable_tasks(tasks, start_date)  # 2. Sort (customizable)

        for task in sorted_tasks:
            updated_task = self._allocate_task(task, context)  # 3. Allocate (customizable)
            if updated_task:
                updated_tasks.append(updated_task)
            else:
                context.record_allocation_failure(task)

        return updated_tasks, context.daily_allocations, context.failed_tasks
```

**Benefits:**
- Eliminates code duplication across 9 strategies
- Ensures consistent behavior (initialization, failure recording, etc.)
- Clear extension points via abstract methods

### Strategy Pattern

Each optimization algorithm is a separate strategy class:

```python
GreedyOptimizationStrategy       # Front-loads tasks (default)
BalancedOptimizationStrategy     # Even workload distribution
BackwardOptimizationStrategy     # Just-in-time from deadlines
PriorityFirstOptimizationStrategy  # Pure priority-based
EarliestDeadlineOptimizationStrategy  # Pure EDF
DependencyAwareOptimizationStrategy  # Critical Path Method
RoundRobinOptimizationStrategy   # Cyclic allocation
GeneticOptimizationStrategy      # Evolutionary algorithm
MonteCarloOptimizationStrategy   # Random sampling
```

Strategies can be selected at runtime via `StrategyFactory`:

```python
strategy = StrategyFactory.create("greedy", default_start_hour=9, default_end_hour=18)
```

### Context Object Pattern

`AllocationContext` encapsulates related parameters and mutable state:

```python
@dataclass
class AllocationContext:
    # Constraints
    start_date: datetime
    max_hours_per_day: float
    holiday_checker: IHolidayChecker | None
    current_time: datetime | None

    # Mutable state
    daily_allocations: dict[date, float]  # Accumulated hours per day
    failed_tasks: list[SchedulingFailure]  # Tasks that couldn't be scheduled
```

**Benefits:**
- Reduces parameter explosion (7 → 2 parameters per method)
- Groups related constraints and state
- Supports nested method calls (Genetic/Monte Carlo strategies)
- Encapsulates initialization logic in `create()` factory

## Core Components

### OptimizationStrategy (Base Class)

**Location:** `packages/taskdog-core/src/taskdog_core/application/services/optimization/optimization_strategy.py`

**Responsibilities:**
- Defines template method `optimize_tasks()`
- Provides protected helper methods for common operations
- Enforces consistent workflow across all strategies

**Abstract Methods (must be implemented by subclasses):**

```python
@abstractmethod
def _allocate_task(self, task: Task, context: AllocationContext) -> Task | None:
    """Allocate time block for a single task."""
    pass
```

**Concrete Methods (can be overridden for custom sorting):**

```python
def _sort_schedulable_tasks(self, tasks: list[Task], start_date: datetime) -> list[Task]:
    """Default: Sort by deadline urgency, priority, task ID."""
    sorter = OptimizationTaskSorter(start_date)
    return sorter.sort_by_priority(tasks)
```

**Protected Helper Methods:**

| Method | Purpose |
|--------|---------|
| `_prepare_task_for_allocation()` | Validates task and creates deep copy |
| `_calculate_available_hours()` | Computes available hours for a date |
| `_set_planned_times()` | Sets planned_start, planned_end, daily_allocations |
| `_rollback_allocations()` | Rolls back failed allocation |

### AllocationContext

**Location:** `packages/taskdog-core/src/taskdog_core/application/services/optimization/allocation_context.py`

**Factory Method:**

```python
context = AllocationContext.create(
    tasks=all_tasks_for_context,  # Tasks to include in workload calculation
    start_date=start_date,
    max_hours_per_day=max_hours_per_day,
    holiday_checker=holiday_checker,
    current_time=current_time,
    workload_calculator=workload_calculator,
)
```

The `create()` factory automatically initializes `daily_allocations` by computing existing workload from scheduled tasks.

**Convenience Methods:**

```python
context.record_failure(task, "Custom reason")
context.record_allocation_failure(task)  # Generic failure message
```

### StrategyFactory

**Location:** `packages/taskdog-core/src/taskdog_core/application/services/optimization/strategy_factory.py`

Creates strategy instances by name:

```python
strategy = StrategyFactory.create(
    algorithm_name="greedy",
    default_start_hour=9,
    default_end_hour=18,
)
```

Supported algorithms: `greedy`, `balanced`, `backward`, `priority_first`, `earliest_deadline`, `dependency_aware`, `round_robin`, `genetic`, `monte_carlo`

### OptimizeScheduleUseCase

**Location:** `packages/taskdog-core/src/taskdog_core/application/use_cases/optimize_schedule.py`

Entry point that:
1. Filters schedulable tasks (`is_schedulable()`)
2. Creates strategy via StrategyFactory
3. Calls `strategy.optimize_tasks()`
4. Returns OptimizationOutput with results

## Optimization Strategies

### Strategy Comparison

| Strategy | Sort Key | Allocation | Use Case |
|----------|----------|------------|----------|
| **Greedy** | Deadline, Priority | Front-loads | Fast completion, default |
| **Balanced** | Deadline, Priority | Even distribution | Work-life balance |
| **Backward** | Deadline (furthest first) | Backward from deadline | Just-in-time, flexibility |
| **PriorityFirst** | Priority only | Front-loads | Ignore deadlines |
| **EarliestDeadline** | Deadline only | Front-loads | Pure EDF |
| **DependencyAware** | Blocking count, Deadline | Front-loads | Critical Path Method |
| **RoundRobin** | None (iteration order) | Cyclic | Fair distribution |
| **Genetic** | Fitness-based | Front-loads | Find global optimum |
| **MonteCarlo** | Random sampling | Front-loads | Probabilistic optimization |

### 1. Greedy (Default)

**Sorting:**
- Primary: Days until deadline (earlier first)
- Secondary: Priority (higher first)
- Tertiary: Task ID

**Allocation:**
- Forward from start_date
- Fills each day to maximum before moving to next

**Characteristics:**
- Fast completion (front-loading)
- Simple and predictable
- Good for tight deadlines

### 2. Balanced

**Sorting:**
- Same as Greedy (deadline, priority)

**Allocation:**
- Distributes hours evenly across available days
- Target hours per day = total_duration / available_weekdays
- Prevents burnout from front-loading

**Characteristics:**
- Better work-life balance
- More realistic workload
- Good for long-term projects

### 3. Backward (Just-In-Time)

**Sorting:**
- Tasks without deadlines first
- Then by deadline (furthest first)

**Allocation:**
- Backward from deadline
- Allocates as late as possible

**Characteristics:**
- Maximum flexibility
- Just-In-Time delivery
- Good when requirements may change

### 4. PriorityFirst

**Sorting:**
- Priority only (high to low)
- Ignores deadlines completely

**Allocation:**
- Inherits from Greedy (front-loads)

**Characteristics:**
- Pure priority-based
- Good for tasks without deadlines
- Focuses on importance over urgency

### 5. EarliestDeadline (EDF)

**Sorting:**
- Deadline only (earliest first)
- Ignores priority completely

**Allocation:**
- Inherits from Greedy (front-loads)

**Characteristics:**
- Pure deadline-based
- Minimizes deadline misses
- Good for time-critical work

### 6. DependencyAware (Critical Path Method)

**Sorting:**
- Primary: Blocking count (tasks that block others first)
- Secondary: Deadline
- Tertiary: Priority

**Allocation:**
- Inherits from Greedy (front-loads)

**Characteristics:**
- Schedules bottleneck tasks first
- Minimizes overall project duration
- Uses task.depends_on relationships

**Example:**
```
Task A depends on Task B and Task C
→ Task B blocks Task A (blocking count = 1)
→ Task C blocks Task A (blocking count = 1)
→ Task B and C scheduled before Task A
```

### 7. RoundRobin

**Sorting:**
- None (uses iteration order)

**Allocation:**
- Cycles through tasks, allocating small chunks
- Distributes time fairly across all tasks

**Characteristics:**
- Fair time distribution
- No starvation (all tasks get time)
- Good for parallel work

### 8. Genetic

**Sorting:**
- Fitness-based (evolutionary)
- Evolves task orderings over generations

**Allocation:**
- Best ordering found after N generations
- Uses Greedy allocation for each ordering

**Characteristics:**
- Finds near-optimal solutions
- Computationally expensive (50 generations × 20 population)
- Good for complex scheduling problems

**Parameters:**
- Population: 20
- Generations: 50
- Crossover rate: 0.8
- Mutation rate: 0.2

### 9. MonteCarlo

**Sorting:**
- Random sampling of orderings
- Evaluates fitness of each sample

**Allocation:**
- Best ordering found after N simulations
- Uses Greedy allocation for each ordering

**Characteristics:**
- Probabilistic optimization
- Computationally expensive (100 simulations)
- Good for exploring solution space

## Data Flow

### Optimization Workflow

```
OptimizeScheduleUseCase
  ↓
  ├─ Filter schedulable tasks (is_schedulable())
  ├─ Create strategy via StrategyFactory
  └─ strategy.optimize_tasks()
       ↓
       ├─ AllocationContext.create() [Initialize daily_allocations]
       ├─ _sort_schedulable_tasks() [Strategy-specific]
       └─ For each task:
            ├─ _allocate_task() [Strategy-specific]
            │   ├─ _prepare_task_for_allocation()
            │   ├─ Find available time slots
            │   ├─ _calculate_available_hours()
            │   ├─ Update context.daily_allocations
            │   └─ _set_planned_times()
            └─ Or: context.record_allocation_failure()
```

### AllocationContext Initialization

```python
AllocationContext.create(tasks=[...])
  ↓
  _initialize_allocations(tasks, workload_calculator)
    ↓
    For each task with schedule:
      ├─ Get task.daily_allocations (if available)
      ├─ Or: workload_calculator.get_task_daily_hours(task)
      └─ Accumulate into daily_allocations dict
```

**Result:** `daily_allocations` contains existing workload before optimization starts.

### Allocation Loop

```python
for task in sorted_tasks:
    # 1. Prepare
    task_copy = _prepare_task_for_allocation(task)
    if not task_copy:
        continue

    # 2. Find time slots
    while remaining_hours > 0:
        available = _calculate_available_hours(daily_allocations, date, ...)
        if available > 0:
            allocated = min(remaining_hours, available)
            daily_allocations[date] += allocated  # Update context
            task_daily_allocations[date] = allocated
            remaining_hours -= allocated

    # 3. Set schedule
    _set_planned_times(task_copy, start, end, task_daily_allocations)
```

## Helper Methods

### `_prepare_task_for_allocation()`

**Purpose:** Validate task and create deep copy for modification

```python
def _prepare_task_for_allocation(self, task: Task) -> Task | None:
    # Validate
    if not task.estimated_duration or task.estimated_duration <= 0:
        return None

    # Deep copy
    task_copy = copy.deepcopy(task)

    # Defensive check
    if task_copy.estimated_duration is None:
        raise ValueError("Cannot allocate task without estimated duration")

    return task_copy
```

**Usage:**
```python
task_copy = self._prepare_task_for_allocation(task)
if task_copy is None:
    return None
assert task_copy.estimated_duration is not None  # Type narrowing for mypy
```

### `_calculate_available_hours()`

**Purpose:** Calculate available hours for a specific date

```python
def _calculate_available_hours(
    self,
    daily_allocations: dict[date, float],
    date_obj: date,
    max_hours_per_day: float,
    current_time: datetime | None,
) -> float:
    current_allocation = daily_allocations.get(date_obj, 0.0)
    available_from_max = max_hours_per_day - current_allocation

    # If today, account for remaining hours
    if current_time and date_obj == current_time.date():
        end_hour = self.default_end_hour
        current_hour = current_time.hour + current_time.minute / 60.0
        remaining_hours_today = max(0.0, end_hour - current_hour)
        return min(available_from_max, remaining_hours_today)

    return available_from_max
```

**Handles:**
- Maximum hours per day constraint
- Already allocated hours
- Remaining hours for today (if current_time provided)

### `_set_planned_times()`

**Purpose:** Set planned_start, planned_end, and daily_allocations on task

```python
def _set_planned_times(
    self,
    task: Task,
    schedule_start: datetime,
    schedule_end: datetime,
    task_daily_allocations: dict[date, float],
) -> None:
    # Set start time to default_start_hour (e.g., 9:00 AM)
    task.planned_start = schedule_start.replace(
        hour=self.default_start_hour, minute=0, second=0
    )

    # Set end time to default_end_hour (e.g., 6:00 PM)
    task.planned_end = schedule_end.replace(
        hour=self.default_end_hour, minute=0, second=0
    )

    # Set daily allocations
    task.set_daily_allocations(task_daily_allocations)
```

### `_rollback_allocations()`

**Purpose:** Rollback failed allocations from daily_allocations

```python
def _rollback_allocations(
    self,
    daily_allocations: dict[date, float],
    task_allocations: dict[date, float],
) -> None:
    for date_obj, hours in task_allocations.items():
        daily_allocations[date_obj] -= hours
```

**Usage:**
```python
task_daily_allocations = {}
# ... allocation logic ...
if failed:
    self._rollback_allocations(context.daily_allocations, task_daily_allocations)
    return None
```

## Extension Guide

### Adding a New Strategy

1. **Create strategy class** (inherit from existing strategy or base class):

```python
from taskdog_core.application.services.optimization.greedy_optimization_strategy import (
    GreedyOptimizationStrategy,
)

class MyCustomOptimizationStrategy(GreedyOptimizationStrategy):
    DISPLAY_NAME = "My Custom"
    DESCRIPTION = "Custom scheduling"

    def _sort_schedulable_tasks(self, tasks, start_date):
        # Custom sorting logic
        return sorted(tasks, key=lambda t: my_custom_key(t))

    # Optionally override _allocate_task() for custom allocation
```

2. **Register in StrategyFactory**:

```python
# packages/taskdog-core/src/taskdog_core/application/services/optimization/strategy_factory.py
STRATEGIES = {
    ...
    "my_custom": MyCustomOptimizationStrategy,
}
```

3. **Add tests**:

```python
# tests/application/services/optimization/test_my_custom_optimization_strategy.py
from tests.application.services.optimization.optimization_strategy_test_base import (
    BaseOptimizationStrategyTest,
)

class TestMyCustomOptimizationStrategy(BaseOptimizationStrategyTest):
    algorithm_name = "my_custom"

    def test_my_custom_behavior(self):
        # ... test custom behavior ...
```

### Using Helper Methods

**Best practice:** Always use base class helpers to avoid code duplication:

```python
def _allocate_task(self, task, context):
    # ✅ GOOD: Use helper
    task_copy = self._prepare_task_for_allocation(task)
    if task_copy is None:
        return None

    # ... allocation logic ...

    available = self._calculate_available_hours(
        context.daily_allocations, date_obj,
        context.max_hours_per_day, context.current_time
    )

    # ✅ GOOD: Use helper
    self._set_planned_times(task_copy, start, end, allocations)
    return task_copy

# ❌ BAD: Duplicate logic
def _allocate_task(self, task, context):
    if not task.estimated_duration or task.estimated_duration <= 0:
        return None
    task_copy = copy.deepcopy(task)
    # ... duplicates _prepare_task_for_allocation logic
```

### Testing Guidelines

**Use BaseOptimizationStrategyTest** for consistent test structure:

```python
class TestMyStrategy(BaseOptimizationStrategyTest):
    algorithm_name = "my_strategy"

    def test_specific_behavior(self):
        # Create tasks
        task = self.create_task("Test", estimated_duration=10.0, deadline=...)

        # Run optimization
        result = self.optimize_schedule(start_date=...)

        # Assert results
        self.assertEqual(len(result.successful_tasks), 1)
        self.assert_task_scheduled(task, expected_start=..., expected_end=...)
```

## Recent Refactorings

### 1. Holiday Checker Bug Fix (Phase 1-1)

**Problem:** GeneticOptimizationStrategy and MonteCarloOptimizationStrategy called non-existent `greedy_strategy._get_holiday_checker()`, causing `holiday_checker` to always be `None`.

**Solution:**
- Added `self.holiday_checker` instance variable
- Store `holiday_checker` in `optimize_tasks()`
- Pass `self.holiday_checker` to temporary contexts

**Impact:** Metaheuristic strategies now properly respect holidays.

### 2. Task Validation Helper Extraction (Phase 2)

**Problem:** Greedy, Balanced, and Backward had identical validation logic (6 lines × 3 = 18 lines duplication).

**Solution:**
- Extracted `_prepare_task_for_allocation()` to base class
- Validates task, creates deep copy, defensive check
- Returns `Task | None`

**Impact:** -15 lines, single source of truth for validation.

### 3. Dead Code Removal (Phase 2)

**Problem:** DependencyAwareOptimizationStrategy had `_calculate_dependency_depths()` that always returned 0 (vestigial from removed parent-child relationships).

**Solution:**
- Removed `_calculate_dependency_depths()` method
- Simplified sorting logic to direct deadline/priority sort

**Impact:** -15 lines, removed confusing dead code.

### 4. Critical Path Method Implementation (Feature)

**Problem:** DependencyAwareOptimizationStrategy was functionally identical to Greedy (sorted by deadline/priority, ignored `depends_on` field).

**Solution:**
- Implemented true Critical Path Method
- Calculate blocking count (how many tasks depend on each task)
- Sort by: blocking count (desc), deadline (asc), priority (desc)
- Tasks blocking others scheduled first

**Impact:** DependencyAware now provides unique value, uses `depends_on` field.

**Example:**
```python
# Before: deadline/priority sort (same as Greedy)
sorted(tasks, key=lambda t: (t.deadline or MAX, -t.priority))

# After: Critical Path Method
blocking_count = {task.id: sum(1 for t in tasks if task.id in t.depends_on)}
sorted(tasks, key=lambda t: (-blocking_count[t.id], t.deadline or MAX, -t.priority))
```

---

## Summary

The optimization system uses a clean Template Method + Strategy pattern architecture:

- **9 different strategies** for different scheduling needs
- **Template Method** eliminates duplication across strategies
- **AllocationContext** manages state and constraints elegantly
- **Helper methods** provide reusable building blocks
- **Easy to extend** with new strategies

This architecture balances flexibility (multiple algorithms) with maintainability (shared infrastructure).
