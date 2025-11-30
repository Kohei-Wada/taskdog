# Taskdog UI Architecture

This document describes the state management architecture used in the Taskdog TUI (Terminal User Interface).

## Overview

The Taskdog TUI uses a **hybrid state management approach** that combines three complementary patterns:

1. **TUIState** - Centralized shared application state
2. **Textual Messages** - Cross-component event notifications
3. **Textual Reactive** - Widget-internal UI state

Each pattern serves a specific purpose and should be used in the appropriate context.

---

## 1. TUIState: Shared Application State

**Location**: `src/taskdog/tui/state/tui_state.py`

**Purpose**: Single Source of Truth (SSoT) for all shared application state.

**What goes in TUIState**:

- Filter settings (e.g., `hide_completed`)
- Sort settings (e.g., `sort_by`, `sort_reverse`)
- Data caches (e.g., `tasks_cache`, `viewmodels_cache`, `gantt_cache`)
- Any state accessed by multiple widgets

**Access pattern**:

```python
# In widgets
from taskdog.tui.app import TaskdogTUI

app = self.app
assert isinstance(app, TaskdogTUI)
value = app.state.hide_completed
```

**Key characteristics**:

- Centralized: All widgets access the same state instance
- Pull-based: Widgets read from state when needed
- Explicit updates: State changes don't automatically trigger UI updates
- Framework-agnostic: Not tied to Textual's reactive system

**When to use**:

- State needs to be accessed by multiple widgets
- State represents application-level configuration
- State needs to survive widget lifecycle
- State needs to be easily testable in isolation

---

## 2. Textual Messages: Cross-Component Notifications

**Location**: `src/taskdog/tui/events.py`

**Purpose**: Notify components about events that occurred elsewhere.

**Current events**:

- `TaskCreated(task_id)` - Task was created
- `TaskUpdated(task_id)` - Task was modified
- `TaskDeleted(task_id)` - Task was removed
- `TasksRefreshed()` - Full task reload needed
- `TaskSelected(task_id)` - User selected a task
- `SearchQueryChanged(query)` - Search query changed
- `GanttResizeRequested(...)` - Gantt recalculation needed

**Usage pattern**:

```python
# Post message
self.post_message(TaskUpdated(task.id))

# Handle message (automatically called by Textual)
def on_task_updated(self, event: TaskUpdated) -> None:
    self._load_tasks(keep_scroll_position=True)
```

**Key characteristics**:

- Decoupled: Sender doesn't know about receivers
- Bubbling: Messages travel up the widget hierarchy
- Multi-listener: Multiple widgets can handle the same message
- Asynchronous: Messages processed via event queue

**When to use**:

- Notifying parent widgets about child events
- Broadcasting events to multiple listeners
- Decoupling components (child doesn't need parent reference)
- Cross-component communication

---

## 3. Textual Reactive: Widget-Internal State

**Purpose**: Manage widget-internal UI state with automatic updates.

**What goes in reactive variables**:

- Search query in SearchInput
- Selection count in TaskTable
- Expanded/collapsed state in widgets
- Any state that only affects one widget's display

**Usage pattern**:

```python
from textual.reactive import reactive

class MyWidget(Widget):
    query = reactive("")  # Reactive variable

    def watch_query(self, old: str, new: str) -> None:
        # Automatically called when query changes
        self._update_display()
```

**Key characteristics**:

- Widget-scoped: State belongs to single widget
- Push-based: Changes automatically trigger watch methods
- Implicit updates: No manual notification needed
- Textual-native: Uses framework's built-in reactivity

**When to use**:

- State only affects one widget
- Want automatic UI updates on state change
- State is purely UI-related (not business logic)
- Widget-internal display state

---

## Decision Matrix: Which Pattern to Use?

| Question | Answer | Pattern |
|----------|--------|---------|
| Does multiple widgets need this state? | Yes | **TUIState** |
| Is this an event notification? | Yes | **Messages** |
| Is this widget-internal UI state? | Yes | **Reactive** |
| Does state need to survive widget lifecycle? | Yes | **TUIState** |
| Want automatic UI updates? | Yes | **Reactive** |
| Need decoupled components? | Yes | **Messages** |

---

## Examples

### Example 1: Hide Completed Tasks

**State**: `TUIState.hide_completed` (shared across app)

**Why TUIState**:

- Multiple widgets need this (TaskTable, GanttWidget)
- Application-level setting
- Needs to survive widget recreation

```python
# In app.py
def action_toggle_completed(self) -> None:
    self.state.hide_completed = not self.state.hide_completed
    self._load_tasks(keep_scroll_position=True)  # Explicit reload
```

### Example 2: Task Update Notification

**Event**: `TaskUpdated` message

**Why Messages**:

- Command executed → notify app → reload data
- Decouples command from app
- App can handle update without command knowing implementation

```python
# In command
self.app.post_message(TaskUpdated(task.id))

# In app.py
def on_task_updated(self, event: TaskUpdated) -> None:
    self._load_tasks(keep_scroll_position=True)
```

### Example 3: Search Query

**State**: `SearchInput.query` reactive variable

**Why Reactive**:

- Only SearchInput cares about this
- Want automatic event posting on change
- Widget-internal UI state

```python
# In search_input.py
class SearchInput(Container):
    query = reactive("")

    def watch_query(self, old: str, new: str) -> None:
        self.post_message(SearchQueryChanged(new))
```

### Example 4: Selection Count Display

**State**: `TaskTable.selection_count` reactive variable

**Why Reactive**:

- Only TaskTable displays this
- Want automatic footer update
- Widget-internal UI state

```python
# In task_table.py
class TaskTable(DataTable):
    selection_count = reactive(0)

    def watch_selection_count(self, old: int, new: int) -> None:
        self._update_selection_display()
```

---

## Anti-Patterns to Avoid

### ❌ Don't use reactive for shared state

```python
# BAD: Other widgets can't access this
class TaskdogTUI(App):
    hide_completed = reactive(False)  # Should be in TUIState
```

### ❌ Don't use TUIState for widget-internal state

```python
# BAD: Pollutes global state
class TUIState:
    search_query: str = ""  # Should be reactive in SearchInput
```

### ❌ Don't use Messages for return values

```python
# BAD: Messages are for notifications, not data transfer
self.post_message(GetTaskResult(task))  # Use direct method call instead
```

### ❌ Don't bypass TUIState

```python
# BAD: State duplication
class TaskTable(DataTable):
    hide_completed: bool = False  # Should use app.state.hide_completed
```

---

## Architecture Evolution

### Phase 1: Scattered State (Before)

- State duplicated across 8+ locations
- Manual synchronization required
- High bug risk

### Phase 2: Centralized State (Current)

- TUIState as Single Source of Truth
- Messages for event notifications
- Eliminated state duplication

### Phase 3: Selective Reactive (Now)

- Widget-internal state uses reactive
- Shared state remains in TUIState
- Hybrid approach for optimal balance

---

## References

- TUIState implementation: `src/taskdog/tui/state/tui_state.py`
- Event definitions: `src/taskdog/tui/events.py`
- Main app: `src/taskdog/tui/app.py`
- Textual reactive docs: https://textual.textualize.io/guide/reactivity/
- Textual messages docs: https://textual.textualize.io/guide/events/
