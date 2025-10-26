#!/usr/bin/env bash
# Launch all multi-agent demo services in separate shells using macOS Terminal.
# Each service runs "uv run ." inside its own package directory so you can stop
# them individually via the Terminal UI (Cmd+W to close window or Ctrl+C).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log() {
	echo -e "[run_demo] $*"
}

start_in_terminal() {
	local name="$1"
	local subdir="$2"
	local cmd="${3:-uv run .}"
	local dir="$SCRIPT_DIR/$subdir"

	if [[ ! -d "$dir" ]]; then
		log "ERROR: Directory not found: $dir"
		return 1
	fi

	# Prefer macOS Terminal to open separate interactive shells the user can stop.
	if command -v osascript >/dev/null 2>&1; then
		osascript <<EOF
tell application "Terminal"
	do script "cd '$dir'; echo '=== $name ==='; uv run ."
end tell
EOF
		log "Launched $name in a new Terminal window"
	else
		# Fallback: run in background within this shell and store PID for optional cleanup.
		(cd "$dir" && echo "=== $name (background) ===" && $cmd) &
		local pid=$!
		echo "$pid" >"$SCRIPT_DIR/.pid_${name//[^A-Za-z0-9]/_}"
		log "Launched $name in background (PID $pid). Use 'kill' to stop it."
	fi
}

log "Starting multi-agent demo services..."

# Weather Agent (defaults to :10001)
start_in_terminal "Weather Agent (:10001)" "weather_agent" "uv run ."

# Airbnb Agent (defaults to :10002)
start_in_terminal "Airbnb Agent (:10002)" "airbnb_agent" "uv run ."

log "Waiting 20 seconds for remote agents to start before launching host agent..."
sleep 20

# Host Agent UI (Gradio, defaults to :8083) - starts last after remote agents are ready
start_in_terminal "Host Agent UI (:8083)" "host_agent" "uv run ."

log "All services launched. If Terminal windows did not open, they are running in background."
log "To stop background services (fallback mode), run:"
log "  pkill -f 'uv run \.'  # stops all uv processes"

