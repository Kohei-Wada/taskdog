# Design Philosophy

This document explains the core design principles behind Taskdog and why certain architectural decisions were made.

## Overview

Taskdog is a **personal task management system** designed for individual users who value simplicity, transparency, and privacy. It combines three interfaces (CLI, TUI, and REST API) with powerful scheduling algorithms while maintaining a flat, dependency-based task structure.

### The Design Journey

Early versions of Taskdog attempted to support parent-child task hierarchies. However, I discovered that this feature:

- Made schedule optimization algorithms unpredictable and complex
- Introduced numerous edge cases in business logic (similar to Redmine's challenges)
- Added implementation complexity without proportional value for individual users

**The key realization**: With only 1-3 concurrent tasks (typical for individuals), parent-child relationships solve a problem that doesn't exist. Dependencies + tags + notes provide sufficient organization without the complexity.

This led to a deliberate decision: **optimize for individual task management**, where flat structure excels.

Unlike team-oriented project management tools (Asana, Jira, ClickUp) or cloud-based AI schedulers (Motion, Reclaim), Taskdog focuses on what individual users truly need: a transparent, offline-capable, and infinitely customizable task manager that doesn't burden them with features designed for teams.

## Target Audience

Taskdog is built for:

- **Individual users** managing personal tasks and projects
- **Engineers and power users** who prefer terminal interfaces
- **Privacy-conscious users** who want local-first data storage
- **GTD practitioners** following Getting Things Done methodology
- **Algorithm enthusiasts** who want to understand and control scheduling logic

Taskdog is **NOT** designed for:

- Team collaboration and project management
- Enterprise workflow orchestration
- Users who prefer graphical interfaces exclusively
- Those seeking fully automated AI scheduling without transparency

## Core Design Principles

### 1. Individual Over Team

**Decision**: Focus exclusively on personal task management.

**Why**:

- Individual users have different needs than teams
- Personal tasks don't require approval workflows, role-based permissions, or team synchronization
- Simpler data models lead to faster performance and easier customization
- Clear market differentiation from team tools

### 2. Flat Structure Over Hierarchy

**Decision**: Use dependencies instead of parent-child relationships (no subtasks).

**Why**:

- Follows GTD philosophy: "Use outlines for planning, plain lists for doing"
- Individual users can mentally track hierarchies without explicit data structures
- Dependencies + tags + notes cover 99% of personal task organization needs
- Keeps optimization algorithms simple and predictable
- Proven approach (Taskwarrior uses the same model)

**Example**: How to manage a complex project like "Website Redesign"

```bash
# Create main tracking task with detailed notes
taskdog add "Website Redesign Project" --tag web --priority 9
taskdog note 1  # Write overall plan, milestones, requirements

# Break down into concrete tasks with dependencies
taskdog add "Requirements gathering" --tag web --priority 8
taskdog add "Design mockups" --tag web --priority 7 --depends-on 2
taskdog add "Frontend implementation" --tag web --priority 6 --depends-on 3
taskdog add "Backend API" --tag web --priority 6 --depends-on 3
taskdog add "Integration testing" --tag web --priority 5 --depends-on 4 5
taskdog add "Deployment" --tag web --priority 4 --depends-on 6

# View the entire project
taskdog table --tag web
taskdog gantt --tag web  # Visualize dependencies
```

**Result**:

- Grouping via tags
- Ordering via dependencies
- Context via markdown notes
- No parent-child hierarchy needed

### 3. Simplicity Over Features

**Decision**: Implement only features that benefit individual task management.

**Why**:

- Feature bloat increases complexity and maintenance burden
- Every feature adds cognitive load for users
- Saying "no" to features is harder but more important than saying "yes"
- Focus creates better user experience for the target audience

**We prioritize**:

- Core task operations (CRUD, status changes)
- Powerful scheduling (9 optimization algorithms)
- Multiple interfaces (CLI, TUI, API)
- Privacy and offline operation

**We explicitly avoid**:

- Team collaboration features
- Complex permission systems
- Cloud synchronization (use git if needed)
- Built-in time tracking (log hours is sufficient)

### 4. Transparency Over Black-box AI

**Decision**: Provide 9 different scheduling algorithms users can understand and choose from.

**Why**:

- Users should understand how their schedule is optimized
- Different situations call for different strategies
- Algorithm selection is a learning opportunity
- No vendor lock-in to proprietary AI

**Available algorithms**:

1. `greedy` - Schedule tasks as early as possible
2. `balanced` - Distribute workload evenly across days
3. `backward` - Schedule from deadlines backward
4. `priority_first` - Always schedule highest priority tasks first
5. `earliest_deadline` - Focus on nearest deadlines
6. `round_robin` - Rotate between different tags
7. `dependency_aware` - Prioritize unblocking other tasks
8. `genetic` - Evolutionary algorithm for global optimization
9. `monte_carlo` - Probabilistic scheduling with randomization

Compare this to Motion/Reclaim: "Our AI schedules your tasks" (black box, no control).

### 5. Privacy Over Cloud

**Decision**: All data stored locally in SQLite, no cloud synchronization.

**Why**:

- Your tasks are your private information
- No dependency on external services
- Works completely offline
- No monthly subscription required
- Full control over your data

**Synchronization options**:

- Git (recommended): Version control for your tasks.db
- File sync: Dropbox, Google Drive, etc. (manual)
- Future: Consider DAT/IPFS for decentralized sync

## Why No Parent-Child Relationships?

**TL;DR**: I tried. It didn't work well for individual task management.

Early versions of Taskdog attempted to support parent-child task hierarchies. However, I found that this feature added significant complexity without proportional value for individual users.

### The Attempt and Why I Abandoned It

When I tried to implement parent-child relationships, I encountered three major problems:

**1. Optimization Algorithms Became Unpredictable**

The core feature of Taskdog is schedule optimization. Parent-child relationships broke this:

```python
# Questions that had no good answers:
- Should we schedule parent tasks?
  → If yes: When? Before children? After? During?
  → If no: How to show them in Gantt chart?

- Is parent's estimated_duration = sum(children)?
  → If yes: What if parent has its own work?
  → If no: How to validate consistency?

- Can we optimize a child independently?
  → If yes: What if it exceeds parent's deadline?
  → If no: Optimization becomes exponentially complex

- What if parent is fixed but children aren't?
  → How to schedule children within parent's fixed time?
```

Every optimization algorithm would need special handling for hierarchies. This made the codebase unmaintainable.

**2. Business Logic Exploded in Complexity**

See the Redmine example in section "Business Logic Complexity" below. I faced the same issues and realized I'd need to make arbitrary decisions for edge cases that had no clear right answer.

**3. Individual Users Didn't Need It**

After removing parent-child relationships, I tested with real workflows. Turns out:

- Dependencies + tags cover 99% of organization needs
- With only 1-3 concurrent tasks, mental hierarchy is sufficient
- The complexity wasn't worth it

**So I made a deliberate choice**: Optimize for individual task management, where parent-child relationships add complexity without value.

This decision led to Taskdog's current positioning: **a tool for individuals, not teams**.

### Additional Context

These observations align with broader industry patterns:

**GTD Philosophy**:
> "The GTD methodology identifies multi-step projects with a desired outcome and a single 'next action' rather than mapping out all dependencies upfront."
> — Getting Things Done Forums

David Allen's GTD approach emphasizes:

- **Planning phase**: Use hierarchical outlines (mental or on paper)
- **Execution phase**: Flat list of "next actions"
- Parent tasks are planning artifacts, not execution items

**Taskwarrior's Approach**:
Taskwarrior, the most successful terminal-based task manager, uses **dependencies only**:

- No native subtask feature
- Community plugins exist but aren't mainstream
- Proven to work for thousands of users over 15+ years

Our experience confirmed what these established approaches already knew: for individual task management, flat structure with dependencies is sufficient.

### Technical Details

**1. Data Model Complexity**

With parent-child relationships:

```python
class Task:
    parent_id: Optional[int]
    children: list[Task]
    depends_on: list[int]

    # Questions arise:
    # - Can a task have both parent AND dependencies?
    # - Is parent.estimated_duration = sum(child.duration)?
    # - What if parent has its own work?
    # - How to handle orphaned children?
```

With dependencies only:

```python
class Task:
    depends_on: list[int]

    # Simple, clear, no edge cases
```

**2. Optimization Algorithm Complexity**

Scheduling with hierarchies:

- Do we schedule parent tasks? If so, when?
- Are parent durations fixed or computed from children?
- Can children be scheduled independently?
- How to handle partial parent completion?

Scheduling with dependencies:

- Clear: schedule tasks whose dependencies are met
- Predictable: algorithms behave consistently
- Testable: easy to verify correctness

**3. UI Complexity**

TUI with hierarchies requires:

- Tree view with expand/collapse
- Indentation management
- Parent-child navigation keybindings
- Filtering becomes complex (show parents without children?)

TUI with flat list:

- Simple table view
- Fast navigation
- Easy filtering and searching
- Familiar interface pattern

**4. Business Logic Complexity**

Parent-child relationships create numerous edge cases and ambiguous behaviors:

**Real-world example: Redmine (team project management tool)**

Redmine supports task hierarchies but faces these issues:

- **Auto-start dilemma**: When you start a child task, should the parent auto-start? If yes, how many levels up?
- **Chain deletion**: If you delete a task in the middle of an IN_PROGRESS chain, what happens to parent and siblings?
- **Orphaned children**: What if parent is deleted but children remain?
- **Circular references**: Child becomes parent of its own ancestor?
- **Status propagation**: If all children are COMPLETED, does parent auto-complete? What about mixed statuses?
- **Estimated duration**: Is parent duration = sum(children) or independent?
- **Assignment**: Can you assign parent without children? Vice versa?

**Each question requires a design decision**, and different tools solve them differently:

- Redmine: Parent doesn't auto-start when children start (surprising to users)
- Jira: Complex permission rules for subtask operations
- Asana: Circular reference detection with multiple algorithms

**With dependencies only**, these questions don't exist:

- Tasks are independent entities
- Dependencies define order, not ownership
- No automatic status propagation
- No ambiguous behavior
- Simpler to test, simpler to understand

**5. Concurrent Task Reality**

**Individual users typically work on 1-3 tasks simultaneously at most**:

- Primary task (currently focused on)
- 1-2 background tasks (waiting, paused, or context-switched)

This is fundamentally different from team projects:

| Scenario | Individual | Team (e.g., 10 people) |
|----------|-----------|------------------------|
| Concurrent IN_PROGRESS tasks | 1-3 tasks | 10-30+ tasks |
| Need for hierarchy | Low (mental tracking) | High (organizational clarity) |
| Task visibility | All in your head | Needs explicit structure |
| Context switching | You decide | Coordinated handoffs |

**Example: Individual developer's day**

```text
9:00  - Start "Implement login API" (IN_PROGRESS)
10:30 - Blocked, waiting for design review
      - Pause, start "Fix bug #123" (IN_PROGRESS)
12:00 - Lunch break
13:00 - Resume "Implement login API"
      - Complete "Fix bug #123"
16:00 - Complete "Implement login API"
```

Only 1-2 tasks active at any moment. **No need for complex hierarchy to track this.**

**Example: Team project (50+ concurrent tasks)**

```text
Epic: User Authentication System
├── Story: Login UI
│   ├── Task: Design mockup (Designer, IN_PROGRESS)
│   ├── Task: Implement form (Frontend Dev, IN_PROGRESS)
│   └── Task: Add validation (Frontend Dev, PENDING)
├── Story: Backend API
│   ├── Task: Database schema (Backend Dev, COMPLETED)
│   ├── Task: API endpoints (Backend Dev, IN_PROGRESS)
│   └── Task: Unit tests (QA, PENDING)
└── Story: Integration
    └── Task: E2E tests (QA, IN_PROGRESS)
```

7+ people, 10+ concurrent tasks. **Hierarchy is necessary for coordination.**

For personal task management with 1-3 concurrent tasks, parent-child relationships add complexity without benefit.

**6. Individual vs. Team Needs**

| Use Case | Individual | Team |
|----------|-----------|------|
| Task hierarchy depth | 1-2 levels | 3-5 levels |
| Who creates subtasks? | Same person | Different people |
| Parent meaning | Mental grouping | Milestone/deliverable |
| Subtask reassignment | N/A | Common |
| Need for structure | Low (in your head) | High (shared understanding) |
| Concurrent tasks | 1-3 tasks | 10-100+ tasks |

For individuals, **mental hierarchy + dependency tracking** is sufficient.

### How to Handle "But I Want Subtasks!"

**Use case**: Break down "Write blog post" into steps.

**Solution 1: Dependencies + Tags**

```bash
taskdog add "Blog: Research topic" --tag blog --priority 8
taskdog add "Blog: Outline" --tag blog --priority 7 --depends-on 1
taskdog add "Blog: Write draft" --tag blog --priority 6 --depends-on 2
taskdog add "Blog: Edit and publish" --tag blog --priority 5 --depends-on 3

taskdog table --tag blog  # See all related tasks
```

**Solution 2: Checklist in Notes**

```bash
taskdog add "Write blog post" --priority 8
taskdog note 1

# In the note (markdown):
## Blog Post: AI Task Management

### Checklist
- [x] Research topic
- [x] Create outline
- [ ] Write introduction
- [ ] Write main sections
- [ ] Conclusion
- [ ] Proofread
- [ ] Publish

### Resources
- Link to research
- Draft ideas
```

**Solution 3: Granular Tasks**

```bash
# Just create 6 tasks, it's fine!
# You're not managing 100 tasks per project
taskdog add "Blog intro" --tag blog
taskdog add "Blog section 1" --tag blog --depends-on 1
# ... etc
```

All three approaches work perfectly without parent-child relationships.

## Comparison with Other Tools

### vs. Taskwarrior

**Similarities**:

- Individual focus
- Dependencies instead of hierarchies
- Terminal-first interface
- Local-first data storage
- Powerful filtering and reporting

**Taskdog advantages**:

- Modern Python codebase (Taskwarrior is C++)
- Multiple optimization algorithms (9 choices)
- Full-featured TUI (taskwarrior-tui is separate project)
- REST API built-in (easy AI integration)
- Simpler data format (SQLite vs. custom format)

**Taskwarrior advantages**:

- Mature ecosystem (15+ years)
- Extensive third-party tools
- Mobile apps (via Taskwarrior Server)
- More filtering capabilities

**Verdict**: Taskdog is "Taskwarrior for the modern era" with AI integration.

### vs. Motion / Reclaim.ai

**Motion/Reclaim approach**:

- Black-box AI scheduling
- Cloud-based SaaS ($19-34/month)
- Requires calendar integration
- Team features available
- No algorithm transparency

**Taskdog approach**:

- 9 transparent algorithms you can understand
- Free and open-source
- Fully offline capable
- Individual-only
- Full API for custom AI integration

**Trade-off**:

- Motion: "Just works" but expensive and opaque
- Taskdog: Requires learning but free and transparent

**Why Taskdog is better for engineers**:

1. You can integrate YOUR choice of AI (ChatGPT, Claude, local LLMs)
2. You understand exactly how scheduling works
3. Your data stays on your machine
4. No monthly fees
5. Fully customizable (it's open source)

### vs. Asana / Jira / ClickUp

**Team tools approach**:

- Rich parent-child task hierarchies
- Team collaboration features
- Complex permission systems
- Cloud-only
- Heavy UI

**Taskdog approach**:

- Flat structure with dependencies
- Individual focus
- Simple data model
- Offline-first
- Lightweight TUI

**When to use which**:

- **Asana/Jira**: Managing team projects with 5+ people
- **Taskdog**: Managing your personal tasks and projects

They serve completely different markets.

## What We Will Add (Future Roadmap)

Features that align with our philosophy:

### Near-term (v0.5-v0.6)

- **Recurring tasks**: Daily/weekly/monthly patterns
- **Task templates**: Quick creation from saved configurations
- **Calendar integration**: iCal export, sync with Google Calendar (read-only)
- **Better search**: Full-text search across names and notes
- **MCP server**: Claude Desktop integration

### Medium-term (v0.7-v0.8)

- **Git integration**: Link tasks to commits/branches
- **Import/export**: From Taskwarrior, org-mode, todo.txt
- **Custom fields**: User-defined attributes
- **Hooks system**: Run scripts on task events

### Long-term (v1.0+)

- **PostgreSQL support**: For power users with massive task counts
- **Plugin system**: Extend functionality without forking
- **Mobile TUI**: Optimized for smaller terminals
- **Natural language input**: "Add task to review PR tomorrow at 2pm"

All future features will be evaluated against our core principles.

## What We Will NOT Add

Features that violate our philosophy:

### Never

- **Parent-child task hierarchies**: Use dependencies + tags + notes instead
- **Team collaboration**: Use Asana/Jira for teams
- **Cloud synchronization**: Use git or file sync
- **Proprietary AI scheduling**: Use open algorithms + API for custom AI
- **Web-based UI**: TUI is the focus (API exists for custom UIs)
- **Time blocking UI**: Use calendar integration + external tools
- **Built-in Pomodoro timer**: Use dedicated tools (e.g., `pomo`)

### Rationale

These features would:

1. Increase complexity beyond individual needs
2. Blur the focus on personal task management
3. Require cloud infrastructure (against privacy principle)
4. Compete poorly with specialized tools
5. Dilute what makes Taskdog unique

## Deployment Philosophy

### Package-First Approach

Taskdog focuses on being a **simple, installable package**:

```bash
# Primary installation method
uv tool install taskdog
uv tool install taskdog-server

# Or via pip
pip install taskdog taskdog-server
```

The repository provides:

- Python packages (taskdog-core, taskdog-server, taskdog-ui)
- systemd/launchd service files for auto-start
- Configuration examples

### What This Repository Does NOT Include

- Docker/container configurations
- Kubernetes manifests
- Reverse proxy configurations
- Authentication/authorization infrastructure
- Backup automation

### Why No Docker in This Repository?

1. **Simplicity**: Individual users don't need containerization for a personal tool
2. **Separation of concerns**: Package distribution ≠ infrastructure management
3. **Avoid over-engineering**: `taskdog-server` runs fine as a simple process

### For Users Who Need Infrastructure

If you need Docker, authentication, reverse proxy, or backup automation, consider creating a separate **taskdog-stack** repository that:

- References taskdog as a dependency
- Adds docker-compose.yml with your preferred setup
- Includes authentication (Authelia, OAuth2 Proxy, etc.)
- Configures reverse proxy (Traefik, Caddy, nginx)
- Sets up backup automation (restic, borg, etc.)

This separation keeps:

- **taskdog**: Simple, focused on the application
- **taskdog-stack**: Infrastructure concerns, customizable per deployment

**Example structure for taskdog-stack**:

```text
taskdog-stack/
├── docker-compose.yml
├── .env.example
├── traefik/
│   └── config.yml
├── authelia/
│   └── configuration.yml
└── backup/
    └── restic.sh
```

This approach follows the Unix philosophy: do one thing well.

## Contributing Within the Philosophy

If you want to contribute to Taskdog, ask yourself:

1. **Does this benefit individual users?** (Not teams)
2. **Does this maintain simplicity?** (Every feature has a cost)
3. **Is this transparent?** (No black boxes)
4. **Does this respect privacy?** (No cloud requirements)
5. **Can this be achieved with existing features?** (Tags, dependencies, notes)

Examples:

**Good contributions**:

- New optimization algorithm (transparent, individual-focused)
- Better TUI keybindings (improves core experience)
- Import from other task managers (helps migration)
- Performance improvements (benefits everyone)
- Bug fixes (always welcome)

**Contributions we'd decline**:

- "Add subtasks/parent-child relationships" (violates flat structure principle)
- "Add real-time team collaboration" (not for individuals)
- "Add cloud sync service" (privacy violation)
- "Replace algorithms with single AI" (opacity)

When in doubt, open a discussion issue first!

## Conclusion

Taskdog's design philosophy can be summarized in one sentence:

> **A transparent, privacy-respecting task manager for individuals who want to understand and control how their time is optimized.**

We believe that:

- Individuals deserve tools designed for them, not dumbed-down team tools
- Transparency beats black-box AI for users who want to learn
- Simplicity and focus create better experiences than feature bloat
- Your tasks are your data, stored on your machine

If this philosophy resonates with you, welcome to Taskdog! If you need team features, cloud sync, or don't want to learn how scheduling works, other excellent tools exist (and that's okay).

---

**Questions or feedback?** Open an issue or discussion on GitHub. We'd love to hear your thoughts on this design philosophy.

**Want to understand the technical architecture?** See [CLAUDE.md](CLAUDE.md) for detailed implementation notes.
