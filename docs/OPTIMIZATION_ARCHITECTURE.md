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

- **OptimizationStrategy** - Abstract base class defining the interface
- **GreedyBasedOptimizationStrategy** - Template Method base class for greedy-based strategies
- **allocation_helpers** - Module with helper functions for task allocation
- **StrategyFactory** - Creates strategy instances by name
- **OptimizeScheduleUseCase** - Entry point orchestrating the optimization

## Architecture Patterns

### Template Method Pattern

The `GreedyBasedOptimizationStrategy` class defines the common workflow while allowing strategies to customize specific steps:

```python
class GreedyBasedOptimizationStrategy(OptimizationStrategy):
    def optimize_tasks(self, tasks, existing_allocations, params) -> OptimizeResult:
        # Template method defining the workflow
        daily_allocations = dict(existing_allocations)  # 1. Copy pre-computed allocations
        result = OptimizeResult(daily_allocations=daily_allocations)

        sorted_tasks = self._sort_tasks(tasks, params.start_date)  # 2. Sort (customizable)

        for task in sorted_tasks:
            updated_task = self._allocate_task(task, daily_allocations, params)  # 3. Allocate
            if updated_task:
                result.tasks.append(updated_task)
            else:
                result.record_allocation_failure(task)

        return result
```

**Benefits:**

- Eliminates code duplication across greedy-based strategies
- Ensures consistent behavior (initialization, failure recording, etc.)
- Clear extension points via virtual methods (`_sort_tasks`)

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
strategy = StrategyFactory.create("greedy")
```

### Parameter Object Pattern

`OptimizeParams` encapsulates optimization constraints as a data transfer object:

```python
@dataclass
class OptimizeParams:
    start_date: datetime
    max_hours_per_day: float
    holiday_checker: IHolidayChecker | None = None
    include_all_days: bool = False
```

`OptimizeResult` encapsulates the optimization output:

```python
@dataclass
class OptimizeResult:
    tasks: list[Task] = field(default_factory=list)  # Successfully scheduled tasks
    daily_allocations: dict[date, float] = field(default_factory=dict)  # Accumulated hours
    failures: list[SchedulingFailure] = field(default_factory=list)  # Failed tasks
```

**Benefits:**

- Reduces parameter explosion via DTOs
- Groups related constraints (input) and results (output)
- Supports nested method calls (Genetic/Monte Carlo strategies)

## Core Components

### OptimizationStrategy (Abstract Base Class)

**Location:** `packages/taskdog-core/src/taskdog_core/application/services/optimization/optimization_strategy.py`

**Responsibilities:**

- Defines abstract `optimize_tasks()` method
- Enforces DISPLAY_NAME and DESCRIPTION class variables
- Provides the interface for all optimization strategies

**Abstract Methods (must be implemented by subclasses):**

```python
@abstractmethod
def optimize_tasks(
    self,
    tasks: list[Task],
    existing_allocations: dict[date, float],
    params: OptimizeParams,
) -> OptimizeResult:
    """Optimize task schedules."""
    pass
```

### GreedyBasedOptimizationStrategy (Template Method Base Class)

**Location:** `packages/taskdog-core/src/taskdog_core/application/services/optimization/greedy_based_optimization_strategy.py`

**Responsibilities:**

- Implements the template method `optimize_tasks()`
- Provides greedy forward allocation algorithm
- Allows subclasses to customize sorting via `_sort_tasks()`

**Virtual Methods (can be overridden for custom sorting):**

```python
def _sort_tasks(self, tasks: list[Task], start_date: datetime) -> list[Task]:
    """Default: Sort by deadline urgency, priority, task ID."""
    sorter = OptimizationTaskSorter(start_date)
    return sorter.sort_by_priority(tasks)
```

### Allocation Helpers (Module Functions)

**Location:** `packages/taskdog-core/src/taskdog_core/application/services/optimization/allocation_helpers.py`

**Functions:**

| Function | Purpose |
|----------|---------|
| `prepare_task_for_allocation()` | Validates task and creates deep copy |
| `calculate_available_hours()` | Computes available hours for a date |
| `set_planned_times()` | Sets planned_start, planned_end, daily_allocations |

### OptimizeParams (Input DTO)

**Location:** `packages/taskdog-core/src/taskdog_core/application/dto/optimize_params.py`

Contains optimization constraints passed from UseCase to Strategy.

### OptimizeResult (Output DTO)

**Location:** `packages/taskdog-core/src/taskdog_core/application/dto/optimize_result.py`

Contains optimization results including scheduled tasks, allocations, and failures.

**Convenience Method:**

```python
result.record_allocation_failure(task)  # Records failure with generic message
```

### StrategyFactory

**Location:** `packages/taskdog-core/src/taskdog_core/application/services/optimization/strategy_factory.py`

Creates strategy instances by name:

```python
strategy = StrategyFactory.create(
    algorithm_name="greedy",
)
```

Supported algorithms: `greedy`, `balanced`, `backward`, `priority_first`, `earliest_deadline`, `dependency_aware`, `round_robin`, `genetic`, `monte_carlo`

### OptimizeScheduleUseCase

**Location:** `packages/taskdog-core/src/taskdog_core/application/use_cases/optimize_schedule.py`

Entry point that:

1. Validates and filters schedulable tasks (`validate_schedulable()`)
2. Pre-computes existing allocations via SQL aggregation (`repository.get_aggregated_daily_allocations()`)
3. Creates strategy via StrategyFactory
4. Creates OptimizeParams DTO with constraints
5. Calls `strategy.optimize_tasks(tasks, existing_allocations, params)`
6. Saves results and returns OptimizationOutput

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

```text
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

```text
OptimizeScheduleUseCase
  ↓
  ├─ Validate schedulable tasks (validate_schedulable())
  ├─ Filter workload tasks (_filter_workload_tasks())
  ├─ Pre-compute allocations (repository.get_aggregated_daily_allocations())
  ├─ Create strategy via StrategyFactory
  ├─ Create OptimizeParams DTO
  └─ strategy.optimize_tasks(tasks, existing_allocations, params)
       ↓
       ├─ Copy existing_allocations to daily_allocations
       ├─ Create OptimizeResult
       ├─ _sort_tasks() [Strategy-specific]
       └─ For each task:
            ├─ _allocate_task(task, daily_allocations, params)
            │   ├─ prepare_task_for_allocation()
            │   ├─ Find available time slots
            │   ├─ calculate_available_hours()
            │   ├─ Update daily_allocations
            │   └─ set_planned_times()
            └─ Or: result.record_allocation_failure()
```

### Existing Allocations Pre-computation

```python
# UseCase pre-computes via SQL aggregation for performance
workload_task_ids = [t.id for t in workload_tasks if t.id is not None]
existing_allocations = repository.get_aggregated_daily_allocations(workload_task_ids)
```

**Result:** `existing_allocations` contains pre-aggregated workload before optimization starts.
This uses SQL SUM/GROUP BY instead of Python loops for better performance.

### Allocation Loop

```python
for task in sorted_tasks:
    # 1. Prepare
    task_copy = prepare_task_for_allocation(task)
    if task_copy is None:
        continue

    # 2. Find time slots
    while remaining_hours > 0:
        available = calculate_available_hours(
            daily_allocations, date_obj,
            params.max_hours_per_day
        )
        if available > 0:
            allocated = min(remaining_hours, available)
            daily_allocations[date_obj] += allocated
            task_daily_allocations[date_obj] = allocated
            remaining_hours -= allocated

    # 3. Set schedule
    set_planned_times(
        task_copy, schedule_start, schedule_end,
        task_daily_allocations
    )
```

## Helper Functions

**Location:** `packages/taskdog-core/src/taskdog_core/application/services/optimization/allocation_helpers.py`

### `prepare_task_for_allocation()`

**Purpose:** Validate task and create deep copy for modification

```python
def prepare_task_for_allocation(task: Task) -> Task | None:
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
task_copy = prepare_task_for_allocation(task)
if task_copy is None:
    return None
assert task_copy.estimated_duration is not None  # Type narrowing for mypy
```

### `calculate_available_hours()`

**Purpose:** Calculate available hours for a specific date

```python
def calculate_available_hours(
    daily_allocations: dict[date, float],
    date_obj: date,
    max_hours_per_day: float,
) -> float:
    current_allocation = daily_allocations.get(date_obj, 0.0)
    return max_hours_per_day - current_allocation
```

**Handles:**

- Maximum hours per day constraint
- Already allocated hours

### `set_planned_times()`

**Purpose:** Set planned_start, planned_end, and daily_allocations on task

```python
def set_planned_times(
    task: Task,
    schedule_start: datetime,
    schedule_end: datetime,
    task_daily_allocations: dict[date, float],
) -> None:
    # Set planned start and end dates
    task.planned_start = schedule_start
    task.planned_end = schedule_end

    # Set daily allocations
    task.set_daily_allocations(task_daily_allocations)
```

### Inline Rollback

Rollback is done inline within the allocation method when deadline is exceeded:

```python
if effective_deadline and current_date > effective_deadline:
    # Rollback any partial allocations
    for date_obj, hours in task_daily_allocations.items():
        daily_allocations[date_obj] -= hours
    return None
```

## Extension Guide

### Adding a New Strategy

1. **Create strategy class** (inherit from existing strategy or base class):

```python
from taskdog_core.application.services.optimization.greedy_based_optimization_strategy import (
    GreedyBasedOptimizationStrategy,
)

class MyCustomOptimizationStrategy(GreedyBasedOptimizationStrategy):
    DISPLAY_NAME = "My Custom"
    DESCRIPTION = "Custom scheduling"

    def _sort_tasks(self, tasks, start_date):
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

### Using Helper Functions

**Best practice:** Always use helper functions from `allocation_helpers.py` to avoid code duplication:

```python
from taskdog_core.application.services.optimization.allocation_helpers import (
    calculate_available_hours,
    prepare_task_for_allocation,
    set_planned_times,
)

def _allocate_task(self, task, daily_allocations, params):
    # ✅ GOOD: Use helper function
    task_copy = prepare_task_for_allocation(task)
    if task_copy is None:
        return None

    # ... allocation logic ...

    available = calculate_available_hours(
        daily_allocations, date_obj,
        params.max_hours_per_day
    )

    # ✅ GOOD: Use helper function
    set_planned_times(
        task_copy, start, end, allocations
    )
    return task_copy

# ❌ BAD: Duplicate logic
def _allocate_task(self, task, daily_allocations, params):
    if not task.estimated_duration or task.estimated_duration <= 0:
        return None
    task_copy = copy.deepcopy(task)
    # ... duplicates prepare_task_for_allocation logic
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

### 1. SQL-Based Allocation Pre-computation

**Problem:** Python loops for workload calculation were inefficient for large task sets.

**Solution:**

- UseCase now pre-computes existing allocations via SQL aggregation
- `repository.get_aggregated_daily_allocations()` uses SQL SUM/GROUP BY
- Strategies receive pre-computed `existing_allocations` dict

**Impact:** Better performance, clearer separation of concerns.

### 2. Helper Function Extraction

**Problem:** Greedy, Balanced, and Backward had identical validation/allocation logic duplicated.

**Solution:**

- Extracted helper functions to `allocation_helpers.py` module
- `prepare_task_for_allocation()` validates task and creates deep copy
- `calculate_available_hours()` computes available hours for a date
- `set_planned_times()` sets schedule on task

**Impact:** Single source of truth for allocation logic, easier testing.

### 3. GreedyBasedOptimizationStrategy Base Class

**Problem:** Most strategies shared the same greedy forward allocation algorithm but duplicated code.

**Solution:**

- Created `GreedyBasedOptimizationStrategy` as intermediate base class
- Implements template method `optimize_tasks()`
- Provides `_allocate_task()` with greedy forward allocation
- Subclasses override `_sort_tasks()` for custom sorting

**Impact:** Eliminated duplication across 7 greedy-based strategies.

### 4. Critical Path Method Implementation

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
- **Template Method** (`GreedyBasedOptimizationStrategy`) eliminates duplication across greedy-based strategies
- **Parameter Objects** (`OptimizeParams`, `OptimizeResult`) manage input/output cleanly
- **Helper functions** (`allocation_helpers.py`) provide reusable building blocks
- **SQL pre-computation** improves performance for workload calculations
- **Easy to extend** with new strategies

This architecture balances flexibility (multiple algorithms) with maintainability (shared infrastructure).
