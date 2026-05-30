# taskdog TUI demo —
#   launch → add a task → search/find it → start → done →
#   sort toggle → command palette → optimize → Gantt repaints.
#
# Recording prep (server + seed must be running BEFORE vhs):
#   Run against an ISOLATED server/db on port 8765 so the real
#   tasks.db and the systemd server (:8000) are never touched.
#     DATA=$(mktemp -d) CONF=$(mktemp -d)
#     mkdir -p $CONF/taskdog
#     printf '[ui]\ntheme = "rose-pine"\n' > $CONF/taskdog/cli.toml
#     XDG_DATA_HOME=$DATA XDG_CONFIG_HOME=$CONF \
#       taskdog-server --host 127.0.0.1 --port 8765 &
#     python scripts/demo_data.py --host 127.0.0.1 --port 8765 -y --no-optimize
#     XDG_CONFIG_HOME=$CONF TASKDOG_API_HOST=127.0.0.1 TASKDOG_API_PORT=8765 \
#       vhs vhs/demo.tape           # → assets/demo.mp4

Output assets/demo.mp4

Set FontSize 16
Set Width 2400
Set Height 1350
Set Framerate 24
Set Theme "rose-pine"
Set TypingSpeed 60ms
Set PlaybackSpeed 1.0

# Launch the TUI against the seeded demo server (~50 tasks).
Type "taskdog tui"
Enter
Sleep 3s

# --- Add a task ---
# `a` opens the form. Name is required; one Tab moves to Duration.
Type "a"
Sleep 1200ms
Type "Ship release notes"
Sleep 400ms
Tab
Type "3"
Sleep 600ms
# Ctrl+S submits the form.
Ctrl+S
Sleep 2s

# --- Find it, then walk it through its lifecycle ---
# `/` focuses the search box; typing filters the table live.
Type "/"
Sleep 500ms
Type "Ship release"
Sleep 1s
# Enter returns focus to the (now single-row) table.
Enter
Sleep 800ms
# `s` starts the task (PENDING -> IN_PROGRESS).
Type "s"
Sleep 1800ms
# `d` completes it (IN_PROGRESS -> COMPLETED, shown struck through).
Type "d"
Sleep 1800ms
# Escape clears the search filter and shows everything again.
Escape
Sleep 1500ms

# --- Focus the Gantt chart and maximize it ---
# Ctrl+K moves focus to the previous widget (the Gantt, above the table);
# `z` maximizes the focused widget to full screen.
Ctrl+K
Sleep 800ms
Type "z"
Sleep 2s

# --- Optimize the whole schedule (repaints the fullscreen Gantt) ---
# Ctrl+P opens the command palette; "optimize" filters to the command.
Ctrl+P
Sleep 600ms
Type "optimize"
Sleep 800ms
Enter
Sleep 1200ms
# Dialog opens focused on the algorithm select (Greedy by default).
# Ctrl+J moves to the required "Max Hours per Day" field; fill it.
Ctrl+J
Sleep 500ms
Type "8"
Sleep 800ms
# Ctrl+J past Start Date (pre-filled) to the "Override existing
# schedules" checkbox; Space turns it on so every task is rescheduled
# (otherwise already-scheduled demo tasks are skipped).
Ctrl+J
Sleep 400ms
Ctrl+J
Sleep 400ms
Space
Sleep 800ms
# Ctrl+S runs the optimizer.
Ctrl+S
Sleep 2s

# Let the Gantt chart settle into its optimized schedule.
Sleep 5s

Type "q"
Sleep 400ms
