#!/bin/bash
# Demo data script for Taskdog
# Creates realistic sample tasks with deadlines, estimates, tags, and dependencies

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if taskdog is installed
if ! command -v taskdog &> /dev/null; then
    echo -e "${RED}Error: taskdog command not found${NC}"
    echo "Please run: make install"
    exit 1
fi

# Check if taskdog-server is running
if ! curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo -e "${YELLOW}Warning: taskdog-server is not running${NC}"
    echo "Starting taskdog-server is recommended for best performance"
    echo "Run: taskdog-server (or systemctl --user start taskdog-server)"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

# Calculate dates relative to today (using date command for Linux/macOS compatibility)
TODAY=$(date +%Y-%m-%d)
TOMORROW=$(date -d "$TODAY + 1 day" +%Y-%m-%d 2>/dev/null || date -v+1d -f %Y-%m-%d "$TODAY" +%Y-%m-%d)
IN_3_DAYS=$(date -d "$TODAY + 3 days" +%Y-%m-%d 2>/dev/null || date -v+3d -f %Y-%m-%d "$TODAY" +%Y-%m-%d)
IN_5_DAYS=$(date -d "$TODAY + 5 days" +%Y-%m-%d 2>/dev/null || date -v+5d -f %Y-%m-%d "$TODAY" +%Y-%m-%d)
IN_1_WEEK=$(date -d "$TODAY + 7 days" +%Y-%m-%d 2>/dev/null || date -v+7d -f %Y-%m-%d "$TODAY" +%Y-%m-%d)
IN_10_DAYS=$(date -d "$TODAY + 10 days" +%Y-%m-%d 2>/dev/null || date -v+10d -f %Y-%m-%d "$TODAY" +%Y-%m-%d)
IN_2_WEEKS=$(date -d "$TODAY + 14 days" +%Y-%m-%d 2>/dev/null || date -v+14d -f %Y-%m-%d "$TODAY" +%Y-%m-%d)
IN_3_WEEKS=$(date -d "$TODAY + 21 days" +%Y-%m-%d 2>/dev/null || date -v+21d -f %Y-%m-%d "$TODAY" +%Y-%m-%d)
IN_1_MONTH=$(date -d "$TODAY + 30 days" +%Y-%m-%d 2>/dev/null || date -v+30d -f %Y-%m-%d "$TODAY" +%Y-%m-%d)
IN_6_WEEKS=$(date -d "$TODAY + 42 days" +%Y-%m-%d 2>/dev/null || date -v+42d -f %Y-%m-%d "$TODAY" +%Y-%m-%d)
IN_2_MONTHS=$(date -d "$TODAY + 60 days" +%Y-%m-%d 2>/dev/null || date -v+60d -f %Y-%m-%d "$TODAY" +%Y-%m-%d)
IN_10_WEEKS=$(date -d "$TODAY + 70 days" +%Y-%m-%d 2>/dev/null || date -v+70d -f %Y-%m-%d "$TODAY" +%Y-%m-%d)
IN_3_MONTHS=$(date -d "$TODAY + 90 days" +%Y-%m-%d 2>/dev/null || date -v+90d -f %Y-%m-%d "$TODAY" +%Y-%m-%d)

# Calculate next Saturday and Sunday
DOW=$(date +%u)  # Day of week (1=Monday, 7=Sunday)
DAYS_UNTIL_SAT=$((6 - DOW))
if [ $DAYS_UNTIL_SAT -lt 0 ]; then DAYS_UNTIL_SAT=$((DAYS_UNTIL_SAT + 7)); fi
DAYS_UNTIL_SUN=$((7 - DOW))
if [ $DAYS_UNTIL_SUN -lt 0 ]; then DAYS_UNTIL_SUN=$((DAYS_UNTIL_SUN + 7)); fi

NEXT_SATURDAY=$(date -d "$TODAY + $DAYS_UNTIL_SAT days" +%Y-%m-%d 2>/dev/null || date -v+${DAYS_UNTIL_SAT}d -f %Y-%m-%d "$TODAY" +%Y-%m-%d)
NEXT_SUNDAY=$(date -d "$TODAY + $DAYS_UNTIL_SUN days" +%Y-%m-%d 2>/dev/null || date -v+${DAYS_UNTIL_SUN}d -f %Y-%m-%d "$TODAY" +%Y-%m-%d)

# Also calculate following weekend
FOLLOWING_SATURDAY=$(date -d "$TODAY + $((DAYS_UNTIL_SAT + 7)) days" +%Y-%m-%d 2>/dev/null || date -v+$((DAYS_UNTIL_SAT + 7))d -f %Y-%m-%d "$TODAY" +%Y-%m-%d)
FOLLOWING_SUNDAY=$(date -d "$TODAY + $((DAYS_UNTIL_SUN + 7)) days" +%Y-%m-%d 2>/dev/null || date -v+$((DAYS_UNTIL_SUN + 7))d -f %Y-%m-%d "$TODAY" +%Y-%m-%d)

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Taskdog Demo Data Script${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "This will create ~25 sample tasks with:"
echo -e "  • Realistic deadlines (from tomorrow to 3 months ahead)"
echo -e "  • Various estimates (2-30 hours)"
echo -e "  • Various tags (work, personal, urgent, etc.)"
echo -e "  • Task dependencies"
echo -e "  • Detailed notes with context and actionable items"
echo -e "  • Some tasks already started/completed"
echo ""
echo -e "${YELLOW}Warning: This will add tasks to your current database${NC}"
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo -e "${GREEN}Creating demo tasks...${NC}"
echo ""

# Function to add task with deadline and estimate
# Usage: add_task_with_details "name" priority "tag1" "tag2" ... "deadline:YYYY-MM-DD" "estimate:HOURS" "note:content" "fixed" "schedule:START END"
add_task_with_details() {
    local name="$1"
    shift

    local priority=""
    local tags=()
    local deadline=""
    local estimate=""
    local depends_on=()
    local note=""
    local fixed=false
    local schedule_start=""
    local schedule_end=""

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            priority:*)
                priority="${1#priority:}"
                ;;
            tag:*)
                tags+=("${1#tag:}")
                ;;
            deadline:*)
                deadline="${1#deadline:}"
                ;;
            estimate:*)
                estimate="${1#estimate:}"
                ;;
            depends:*)
                depends_on+=("${1#depends:}")
                ;;
            note:*)
                note="${1#note:}"
                ;;
            fixed)
                fixed=true
                ;;
            schedule:*)
                # Format: schedule:START END
                local sched="${1#schedule:}"
                schedule_start="${sched%% *}"
                schedule_end="${sched##* }"
                ;;
        esac
        shift
    done

    # Build add command with all parameters
    local cmd="taskdog add \"$name\""
    if [[ -n "$priority" ]]; then
        cmd="$cmd --priority $priority"
    fi
    if [[ -n "$deadline" ]]; then
        cmd="$cmd --deadline \"$deadline\""
    fi
    if [[ -n "$estimate" ]]; then
        cmd="$cmd --estimate $estimate"
    fi
    if [[ "$fixed" == true ]]; then
        cmd="$cmd --fixed"
    fi
    for tag in "${tags[@]}"; do
        cmd="$cmd --tag $tag"
    done
    for dep in "${depends_on[@]}"; do
        cmd="$cmd --depends-on $dep"
    done

    # Execute add command and capture ID
    local output
    output=$(eval "$cmd" 2>&1)
    local task_id
    task_id=$(echo "$output" | grep -oP 'ID: \K\d+')

    if [[ -z "$task_id" ]]; then
        echo "Error creating task: $name" >&2
        echo "$output" >&2
        return 1
    fi

    # Set note if provided (note not yet supported in add command)
    if [[ -n "$note" ]]; then
        taskdog note "$task_id" --content "$note" > /dev/null 2>&1
    fi

    # Set schedule if provided
    if [[ -n "$schedule_start" ]] && [[ -n "$schedule_end" ]]; then
        taskdog schedule "$task_id" "$schedule_start" "$schedule_end" > /dev/null 2>&1
    fi

    echo "✓ Created: $name (ID: $task_id)"
    echo "$task_id"
}

# ============================================================================
# Project: Web Application Development
# ============================================================================

echo -e "${BLUE}[Project: Web Application Development]${NC}"

# Phase 1: Planning & Design
T1=$(add_task_with_details "Project kickoff meeting" priority:4 tag:work tag:planning deadline:"$TOMORROW" estimate:2 note:"Gather all stakeholders to discuss project scope, timeline, and deliverables. Prepare agenda: goals, tech stack, roles & responsibilities." | tail -1)
T2=$(add_task_with_details "Define API specifications" priority:4 tag:work tag:backend tag:docs deadline:"$IN_3_DAYS" estimate:4 note:"Document all REST API endpoints with request/response schemas. Use OpenAPI 3.0 format. Include authentication flow and error codes." | tail -1)
T3=$(add_task_with_details "Design database schema" priority:5 tag:work tag:backend tag:urgent deadline:"$IN_3_DAYS" estimate:6 note:"Create ER diagram for core entities: users, tasks, projects. Define indexes, foreign keys, and constraints. Consider normalization and query performance." | tail -1)
T4=$(add_task_with_details "Create UI/UX mockups" priority:3 tag:work tag:frontend tag:design deadline:"$IN_5_DAYS" estimate:8 note:"Design wireframes for main pages: dashboard, task list, task details. Use Figma. Focus on mobile-first responsive design." | tail -1)

# Phase 2: Backend Development
T5=$(add_task_with_details "Setup development environment" priority:5 tag:work tag:backend tag:devops deadline:"$IN_5_DAYS" estimate:3 note:"Configure Docker containers for local dev. Setup PostgreSQL, Redis. Create docker-compose.yml with hot-reload support." | tail -1)
T6=$(add_task_with_details "Implement user authentication" priority:5 tag:work tag:backend tag:security deadline:"$IN_1_WEEK" estimate:8 note:"Implement JWT-based auth with refresh tokens. Add password hashing (bcrypt). Include email verification and password reset flows." | tail -1)
T7=$(add_task_with_details "Create REST API endpoints" priority:4 tag:work tag:backend deadline:"$IN_10_DAYS" estimate:12 note:"Build CRUD endpoints for tasks, projects, users. Implement filtering, sorting, pagination. Add input validation and error handling." | tail -1)

# Phase 3: Frontend Development
T8=$(add_task_with_details "Setup React project structure" priority:4 tag:work tag:frontend deadline:"$IN_1_WEEK" estimate:3 note:"Initialize Vite + React + TypeScript project. Setup ESLint, Prettier. Configure routing (React Router), state management (Zustand), and API client (Axios)." | tail -1)
T9=$(add_task_with_details "Implement login/signup pages" priority:5 tag:work tag:frontend deadline:"$IN_10_DAYS" estimate:6 note:"Create forms with validation (react-hook-form + zod). Handle JWT storage. Add social login buttons (Google, GitHub). Show error messages." | tail -1)
T10=$(add_task_with_details "Build dashboard components" priority:4 tag:work tag:frontend deadline:"$IN_2_WEEKS" estimate:10 note:"Create reusable components: TaskCard, TaskList, ProjectCard, StatisticsWidget. Implement drag-and-drop for task ordering. Add real-time updates via WebSocket." | tail -1)
T11=$(add_task_with_details "Add responsive design" priority:3 tag:work tag:frontend tag:design deadline:"$IN_2_WEEKS" estimate:8 note:"Apply Tailwind CSS breakpoints for mobile/tablet/desktop. Test on different screen sizes. Ensure touch-friendly UI on mobile devices." | tail -1)

# Phase 4: Testing & Deployment
T12=$(add_task_with_details "Write unit tests" priority:4 tag:work tag:testing deadline:"$IN_2_WEEKS" estimate:8 note:"Write Jest tests for backend services and API routes. Aim for 80% code coverage. Mock database and external services. Test edge cases and error handling." | tail -1)
T13=$(add_task_with_details "Perform integration testing" priority:5 tag:work tag:testing tag:urgent deadline:"$IN_3_WEEKS" estimate:6 note:"Test end-to-end user flows with Playwright. Cover auth, CRUD operations, real-time updates. Test on Chrome, Firefox, Safari." | tail -1)
T14=$(add_task_with_details "Setup CI/CD pipeline" priority:3 tag:work tag:devops deadline:"$IN_3_WEEKS" estimate:5 note:"Configure GitHub Actions for automated testing and deployment. Run tests on PR. Auto-deploy to staging on merge to main. Manual approval for prod." | tail -1)
T15=$(add_task_with_details "Deploy to production" priority:5 tag:work tag:devops tag:urgent deadline:"$IN_1_MONTH" estimate:4 note:"Deploy to AWS ECS with load balancer. Configure SSL certificates. Setup database backups. Monitor logs and metrics with CloudWatch." | tail -1)

# ============================================================================
# Bug Fixes & Improvements
# ============================================================================

echo -e "${BLUE}[Bug Fixes & Improvements]${NC}"

T16=$(add_task_with_details "Fix login page CSS issues" priority:4 tag:work tag:bugfix tag:frontend tag:urgent deadline:"$TOMORROW" estimate:2 note:"Login button is misaligned on mobile. Form labels are cut off on narrow screens. Fix z-index issues with password visibility toggle." | tail -1)
T17=$(add_task_with_details "Optimize database queries" priority:3 tag:work tag:backend tag:performance deadline:"$IN_1_WEEK" estimate:4 note:"Add indexes on frequently queried columns (user_id, created_at). Implement connection pooling. Use EXPLAIN ANALYZE to identify slow queries. Consider adding Redis cache." | tail -1)

# ============================================================================
# Documentation & Maintenance
# ============================================================================

echo -e "${BLUE}[Documentation & Maintenance]${NC}"

T18=$(add_task_with_details "Update README.md" priority:2 tag:work tag:docs deadline:"$IN_2_WEEKS" estimate:2 note:"Add setup instructions, environment variables, and deployment guide. Include screenshots. Update API examples. Add troubleshooting section." | tail -1)

# ============================================================================
# Long-term Projects (2-3 months ahead)
# ============================================================================

echo -e "${BLUE}[Long-term Projects]${NC}"

# Version 2.0 Planning
T19=$(add_task_with_details "Plan version 2.0 features" priority:3 tag:work tag:planning tag:v2 deadline:"$IN_6_WEEKS" estimate:8 note:"Gather user feedback from v1.0. Prioritize features: advanced filters, custom views, team collaboration, mobile app. Create product roadmap." | tail -1)
T20=$(add_task_with_details "Research new technology stack" priority:2 tag:work tag:research tag:v2 deadline:"$IN_2_MONTHS" estimate:12 note:"Evaluate alternatives: Remix vs Next.js 14, tRPC vs GraphQL, Prisma vs Drizzle ORM. Consider serverless architecture. Create comparison matrix." | tail -1)

# Security & Infrastructure
T21=$(add_task_with_details "Conduct security audit" priority:4 tag:work tag:security tag:audit deadline:"$IN_6_WEEKS" estimate:10 note:"Run OWASP ZAP scan. Review authentication flows. Check for SQL injection, XSS vulnerabilities. Test rate limiting. Perform penetration testing." | tail -1)
T22=$(add_task_with_details "Setup monitoring and alerts" priority:4 tag:work tag:devops tag:monitoring deadline:"$IN_2_MONTHS" estimate:8 note:"Configure Datadog/New Relic for APM. Setup alerts for error rates, response times, CPU/memory usage. Create dashboards for key metrics. Setup PagerDuty integration." | tail -1)

# ============================================================================
# Weekend Fixed Tasks
# ============================================================================

echo -e "${BLUE}[Weekend Fixed Tasks]${NC}"

T23=$(add_task_with_details "Weekend side project coding" priority:2 tag:personal tag:weekend tag:coding deadline:"$NEXT_SUNDAY" estimate:6 fixed "schedule:$NEXT_SATURDAY $NEXT_SUNDAY" note:"Work on personal Rust project. Focus on implementing async runtime and improving error handling. Goal: Complete 2-3 modules." | tail -1)
T24=$(add_task_with_details "Sunday family time" priority:5 tag:personal tag:family tag:weekend deadline:"$NEXT_SUNDAY" estimate:4 fixed "schedule:$NEXT_SUNDAY $NEXT_SUNDAY" note:"Quality time with family. Visit the park, have lunch together, play board games. No work-related activities." | tail -1)
T25=$(add_task_with_details "Weekend on-call duty" priority:4 tag:work tag:oncall tag:weekend deadline:"$FOLLOWING_SUNDAY" estimate:8 fixed "schedule:$FOLLOWING_SATURDAY $FOLLOWING_SUNDAY" note:"On-call rotation for production systems. Monitor alerts, respond to incidents. Keep laptop and phone nearby. Escalate if needed." | tail -1)

echo ""
echo -e "${GREEN}✓ Created 25 tasks${NC}"
echo ""

# ============================================================================
# Add Dependencies
# ============================================================================

echo -e "${BLUE}Adding task dependencies...${NC}"

# Backend development depends on planning
[ -n "$T6" ] && [ -n "$T3" ] && taskdog add-dependency "$T6" "$T3"  # Auth depends on DB schema
[ -n "$T7" ] && [ -n "$T2" ] && taskdog add-dependency "$T7" "$T2"  # API endpoints depend on API spec
[ -n "$T7" ] && [ -n "$T5" ] && taskdog add-dependency "$T7" "$T5"  # API depends on dev env

# Frontend depends on design and backend
[ -n "$T9" ] && [ -n "$T4" ] && taskdog add-dependency "$T9" "$T4"  # Login page depends on mockups
[ -n "$T9" ] && [ -n "$T6" ] && taskdog add-dependency "$T9" "$T6"  # Login depends on auth API
[ -n "$T10" ] && [ -n "$T7" ] && taskdog add-dependency "$T10" "$T7"  # Dashboard depends on API
[ -n "$T11" ] && [ -n "$T10" ] && taskdog add-dependency "$T11" "$T10"  # Responsive design depends on components

# Testing depends on implementation
[ -n "$T12" ] && [ -n "$T7" ] && taskdog add-dependency "$T12" "$T7"  # Unit tests depend on backend
[ -n "$T13" ] && [ -n "$T12" ] && taskdog add-dependency "$T13" "$T12"  # Integration depends on unit tests
[ -n "$T13" ] && [ -n "$T10" ] && taskdog add-dependency "$T13" "$T10"  # Integration depends on frontend

# Deployment depends on everything
[ -n "$T15" ] && [ -n "$T13" ] && taskdog add-dependency "$T15" "$T13"  # Deploy depends on testing
[ -n "$T15" ] && [ -n "$T14" ] && taskdog add-dependency "$T15" "$T14"  # Deploy depends on CI/CD

# Bug fix depends on components
[ -n "$T16" ] && [ -n "$T9" ] && taskdog add-dependency "$T16" "$T9"  # Fix login CSS depends on login page

# Long-term project dependencies
[ -n "$T21" ] && [ -n "$T15" ] && taskdog add-dependency "$T21" "$T15"  # Security audit after deployment

echo ""
echo -e "${GREEN}✓ Added dependencies${NC}"
echo ""

# ============================================================================
# Simulate Progress (mark some tasks as started/completed)
# ============================================================================

echo -e "${BLUE}Simulating project progress...${NC}"

# Mark early tasks as completed
[ -n "$T1" ] && taskdog start "$T1" > /dev/null && taskdog done "$T1" > /dev/null && echo "✓ Completed: Project kickoff meeting"
[ -n "$T2" ] && taskdog start "$T2" > /dev/null && taskdog done "$T2" > /dev/null && echo "✓ Completed: Define API specifications"
[ -n "$T3" ] && taskdog start "$T3" > /dev/null && taskdog done "$T3" > /dev/null && echo "✓ Completed: Design database schema"

# Mark some tasks as in progress
[ -n "$T5" ] && taskdog start "$T5" > /dev/null && echo "⚙ In Progress: Setup development environment"
[ -n "$T6" ] && taskdog start "$T6" > /dev/null && echo "⚙ In Progress: Implement user authentication"
[ -n "$T16" ] && taskdog start "$T16" > /dev/null && echo "⚙ In Progress: Fix login page CSS issues"

echo ""
echo -e "${GREEN}✓ Simulated progress${NC}"
echo ""

# ============================================================================
# Run Optimization
# ============================================================================

echo -e "${BLUE}Running schedule optimization...${NC}"

# Run optimize to auto-schedule pending tasks
taskdog optimize --start-date "$TOMORROW" --max-hours-per-day 8 --algorithm greedy

echo ""
echo -e "${GREEN}✓ Schedule optimization completed${NC}"
echo ""

# ============================================================================
# Display Results
# ============================================================================

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Demo data created successfully!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""
echo "Summary:"
echo "  • 25 tasks created"
echo "  • 3 completed tasks"
echo "  • 3 in-progress tasks"
echo "  • 19 pending tasks"
echo "  • Multiple dependencies configured"
echo "  • Detailed notes for all tasks"
echo "  • Timeline: From tomorrow to 2 months ahead"
echo "  • Estimates: 2-12 hours per task"
echo ""
echo -e "${BLUE}Useful commands:${NC}"
echo "  taskdog table          - View all tasks"
echo "  taskdog gantt          - View Gantt chart"
echo "  taskdog today          - View today's tasks"
echo "  taskdog show <ID>      - View task details with notes"
echo "  taskdog optimize       - Auto-schedule tasks"
echo "  taskdog tui            - Open interactive TUI"
echo ""
echo -e "${BLUE}Viewing current task list:${NC}"
echo ""

# Show the task table
taskdog table --sort deadline
