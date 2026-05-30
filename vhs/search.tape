# taskdog TUI demo — sort then progressively filter a maximized task list.
#   maximize -> sort (palette) + direction -> /-search + Enter
#   -> Ctrl+U re-search -> Ctrl+R progressive filter chain.
#
# The list stays maximized throughout. Escape is intentionally avoided: while
# a widget is maximized Escape only un-maximizes (it does NOT clear the filter
# chain), so the flow uses Enter / Ctrl+U / Ctrl+R and sorts the full list
# first, then narrows down — no clearing needed.
#
# Recording prep (server + seed must be running BEFORE vhs), same isolated
# setup as demo.tape (separate server/db on port 8765, rose-pine theme):
#     DATA=$(mktemp -d) CONF=$(mktemp -d)
#     mkdir -p $CONF/taskdog
#     printf '[ui]\ntheme = "rose-pine"\n' > $CONF/taskdog/cli.toml
#     XDG_DATA_HOME=$DATA XDG_CONFIG_HOME=$CONF \
#       taskdog-server --host 127.0.0.1 --port 8765 &
#     python scripts/demo_data.py --host 127.0.0.1 --port 8765 -y --no-optimize
#     XDG_CONFIG_HOME=$CONF TASKDOG_API_HOST=127.0.0.1 TASKDOG_API_PORT=8765 \
#       vhs vhs/search.tape         # → assets/search.mp4

Output assets/search.mp4

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

# Maximize the task list (the search footer stays docked via
# ALLOW_IN_MAXIMIZED_VIEW) so the whole list is visible.
Type "z"
Sleep 1800ms

# --- Sort the full list (two-stage command palette) ---
# Ctrl+P -> "sort" -> the Sort command -> a second palette of fields.
Ctrl+P
Sleep 600ms
Type "sort"
Sleep 600ms
Enter
Sleep 1000ms
Type "priority"
Sleep 600ms
Enter
Sleep 1800ms
# Ctrl+T flips ascending <-> descending.
Ctrl+T
Sleep 2s

# --- Basic search: type a term, Enter returns focus to the list ---
# Substring match across name, tags, status, etc.
Type "/"
Sleep 500ms
Type "api"
Sleep 2s
Enter
Sleep 1500ms

# --- New search: focus the box, Ctrl+U clears it, then type a new term ---
Type "/"
Sleep 400ms
Ctrl+U
Sleep 400ms
Type "mobile"
Sleep 2s
Enter
Sleep 1500ms

# --- Progressive filter chain (Ctrl+R) ---
# Ctrl+R locks the current query into the filter chain and clears the input
# for the next one; each link is AND-ed, narrowing the list step by step.
Type "/"
Sleep 400ms
Ctrl+U
Sleep 300ms
Type "work"
Sleep 1200ms
Ctrl+R
Sleep 1500ms
Type "!completed"
Sleep 1200ms
Ctrl+R
Sleep 1500ms
Type "!tag:urgent"
Sleep 2200ms
Enter
Sleep 2s

Type "q"
Sleep 400ms
