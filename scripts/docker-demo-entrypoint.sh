#!/bin/bash
set -e

# Start taskdog-server in background
taskdog-server --host 0.0.0.0 --port 8000 &
SERVER_PID=$!

# Wait for server to be ready
echo "Starting taskdog-server..."
for i in $(seq 1 30); do
    if python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" 2>/dev/null; then
        break
    fi
    sleep 0.5
done

# Load demo data
echo "Loading demo data..."
python scripts/demo_data.py -y

if [ -t 0 ]; then
    # Interactive mode: launch TUI
    exec taskdog tui
else
    # Detached mode: keep server running
    echo "Server ready at http://localhost:8000"
    echo "Connect with: uvx --from taskdog-ui taskdog tui"
    wait $SERVER_PID
fi
