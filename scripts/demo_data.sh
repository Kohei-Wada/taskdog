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

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Taskdog Demo Data Script${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "This will create ~25 sample tasks with:"
echo -e "  • Realistic deadlines (from tomorrow to 3 months ahead)"
echo -e "  • Various estimates (2-30 hours)"
echo -e "  • Various tags (work, personal, urgent, etc.)"
echo -e "  • Task dependencies"
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
# Usage: add_task_with_details "name" priority "tag1" "tag2" ... "deadline:YYYY-MM-DD" "estimate:HOURS"
add_task_with_details() {
    local name="$1"
    shift

    local priority=""
    local tags=()
    local deadline=""
    local estimate=""
    local depends_on=()

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
        esac
        shift
    done

    # Build add command
    local cmd="taskdog add \"$name\""
    if [[ -n "$priority" ]]; then
        cmd="$cmd --priority $priority"
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

    # Set deadline if provided
    if [[ -n "$deadline" ]]; then
        taskdog deadline "$task_id" "$deadline" > /dev/null 2>&1
    fi

    # Set estimate if provided
    if [[ -n "$estimate" ]]; then
        taskdog estimate "$task_id" "$estimate" > /dev/null 2>&1
    fi

    echo "✓ Created: $name (ID: $task_id)"
    echo "$task_id"
}

# ============================================================================
# Project: Web Application Development
# ============================================================================

echo -e "${BLUE}[Project: Web Application Development]${NC}"

# Phase 1: Planning & Design
T1=$(add_task_with_details "Project kickoff meeting" priority:4 tag:work tag:planning deadline:"$TOMORROW" estimate:2 | tail -1)
T2=$(add_task_with_details "Define API specifications" priority:4 tag:work tag:backend tag:docs deadline:"$IN_3_DAYS" estimate:4 | tail -1)
T3=$(add_task_with_details "Design database schema" priority:5 tag:work tag:backend tag:urgent deadline:"$IN_3_DAYS" estimate:6 | tail -1)
T4=$(add_task_with_details "Create UI/UX mockups" priority:3 tag:work tag:frontend tag:design deadline:"$IN_5_DAYS" estimate:8 | tail -1)

# Phase 2: Backend Development
T5=$(add_task_with_details "Setup development environment" priority:5 tag:work tag:backend tag:devops deadline:"$IN_5_DAYS" estimate:3 | tail -1)
T6=$(add_task_with_details "Implement user authentication" priority:5 tag:work tag:backend tag:security deadline:"$IN_1_WEEK" estimate:8 | tail -1)
T7=$(add_task_with_details "Create REST API endpoints" priority:4 tag:work tag:backend deadline:"$IN_10_DAYS" estimate:12 | tail -1)
T8=$(add_task_with_details "Write API documentation" priority:3 tag:work tag:docs deadline:"$IN_10_DAYS" estimate:4 | tail -1)

# Phase 3: Frontend Development
T9=$(add_task_with_details "Setup React project structure" priority:4 tag:work tag:frontend deadline:"$IN_1_WEEK" estimate:3 | tail -1)
T10=$(add_task_with_details "Implement login/signup pages" priority:5 tag:work tag:frontend deadline:"$IN_10_DAYS" estimate:6 | tail -1)
T11=$(add_task_with_details "Build dashboard components" priority:4 tag:work tag:frontend deadline:"$IN_2_WEEKS" estimate:10 | tail -1)
T12=$(add_task_with_details "Add responsive design" priority:3 tag:work tag:frontend tag:design deadline:"$IN_2_WEEKS" estimate:8 | tail -1)

# Phase 4: Testing & Deployment
T13=$(add_task_with_details "Write unit tests" priority:4 tag:work tag:testing deadline:"$IN_2_WEEKS" estimate:8 | tail -1)
T14=$(add_task_with_details "Perform integration testing" priority:5 tag:work tag:testing tag:urgent deadline:"$IN_3_WEEKS" estimate:6 | tail -1)
T15=$(add_task_with_details "Setup CI/CD pipeline" priority:3 tag:work tag:devops deadline:"$IN_3_WEEKS" estimate:5 | tail -1)
T16=$(add_task_with_details "Deploy to production" priority:5 tag:work tag:devops tag:urgent deadline:"$IN_1_MONTH" estimate:4 | tail -1)

# ============================================================================
# Bug Fixes & Improvements
# ============================================================================

echo -e "${BLUE}[Bug Fixes & Improvements]${NC}"

T17=$(add_task_with_details "Fix login page CSS issues" priority:4 tag:work tag:bugfix tag:frontend tag:urgent deadline:"$TOMORROW" estimate:2 | tail -1)
T18=$(add_task_with_details "Optimize database queries" priority:3 tag:work tag:backend tag:performance deadline:"$IN_1_WEEK" estimate:4 | tail -1)

# ============================================================================
# Documentation & Maintenance
# ============================================================================

echo -e "${BLUE}[Documentation & Maintenance]${NC}"

T19=$(add_task_with_details "Update README.md" priority:2 tag:work tag:docs deadline:"$IN_2_WEEKS" estimate:2 | tail -1)
T20=$(add_task_with_details "Code review and refactoring" priority:2 tag:work tag:maintenance deadline:"$IN_3_WEEKS" estimate:6 | tail -1)

# ============================================================================
# Personal Tasks
# ============================================================================

echo -e "${BLUE}[Personal Tasks]${NC}"

T21=$(add_task_with_details "Read technical blog posts" priority:1 tag:personal tag:learning deadline:"$IN_1_WEEK" estimate:2 | tail -1)

# ============================================================================
# Long-term Projects (2-3 months ahead)
# ============================================================================

echo -e "${BLUE}[Long-term Projects]${NC}"

# Version 2.0 Planning
T22=$(add_task_with_details "Plan version 2.0 features" priority:3 tag:work tag:planning tag:v2 deadline:"$IN_6_WEEKS" estimate:8 | tail -1)
T23=$(add_task_with_details "Research new technology stack" priority:2 tag:work tag:research tag:v2 deadline:"$IN_2_MONTHS" estimate:12 | tail -1)

# Security & Infrastructure
T24=$(add_task_with_details "Conduct security audit" priority:4 tag:work tag:security tag:audit deadline:"$IN_6_WEEKS" estimate:10 | tail -1)
T25=$(add_task_with_details "Setup monitoring and alerts" priority:4 tag:work tag:devops tag:monitoring deadline:"$IN_2_MONTHS" estimate:8 | tail -1)

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
[ -n "$T10" ] && [ -n "$T4" ] && taskdog add-dependency "$T10" "$T4"  # Login page depends on mockups
[ -n "$T10" ] && [ -n "$T6" ] && taskdog add-dependency "$T10" "$T6"  # Login depends on auth API
[ -n "$T11" ] && [ -n "$T7" ] && taskdog add-dependency "$T11" "$T7"  # Dashboard depends on API
[ -n "$T12" ] && [ -n "$T11" ] && taskdog add-dependency "$T12" "$T11"  # Responsive design depends on components

# Testing depends on implementation
[ -n "$T13" ] && [ -n "$T7" ] && taskdog add-dependency "$T13" "$T7"  # Unit tests depend on backend
[ -n "$T14" ] && [ -n "$T13" ] && taskdog add-dependency "$T14" "$T13"  # Integration depends on unit tests
[ -n "$T14" ] && [ -n "$T11" ] && taskdog add-dependency "$T14" "$T11"  # Integration depends on frontend

# Deployment depends on everything
[ -n "$T16" ] && [ -n "$T14" ] && taskdog add-dependency "$T16" "$T14"  # Deploy depends on testing
[ -n "$T16" ] && [ -n "$T15" ] && taskdog add-dependency "$T16" "$T15"  # Deploy depends on CI/CD

# Bug fix depends on components
[ -n "$T17" ] && [ -n "$T10" ] && taskdog add-dependency "$T17" "$T10"  # Fix login CSS depends on login page

# Long-term project dependencies
[ -n "$T24" ] && [ -n "$T16" ] && taskdog add-dependency "$T24" "$T16"  # Security audit after deployment

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
[ -n "$T17" ] && taskdog start "$T17" > /dev/null && echo "⚙ In Progress: Fix login page CSS issues"

echo ""
echo -e "${GREEN}✓ Simulated progress${NC}"
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
echo "  • Timeline: From tomorrow to 2 months ahead"
echo "  • Estimates: 2-12 hours per task"
echo ""
echo -e "${BLUE}Useful commands:${NC}"
echo "  taskdog table          - View all tasks"
echo "  taskdog gantt          - View Gantt chart"
echo "  taskdog today          - View today's tasks"
echo "  taskdog optimize       - Auto-schedule tasks"
echo "  taskdog tui            - Open interactive TUI"
echo ""
echo -e "${BLUE}Viewing current task list:${NC}"
echo ""

# Show the task table
taskdog table --sort deadline
