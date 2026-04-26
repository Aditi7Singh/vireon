#!/bin/bash
set -euo pipefail

# Run from repo root
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "🚀 Starting Vireon Agentic CFO Stack..."
	if [[ ! -f "$DIR/backend/.env" ]]; then
		cat <<'EOF'
Missing backend/.env.

Copy backend/.env.example to backend/.env and set the required values,
then run ./start.sh again.
EOF
		exit 1
	fi

ensure_docker_running() {
	if docker info >/dev/null 2>&1; then
		return 0
	fi

	echo "Docker daemon is not reachable on current context."

	# If default context works (for alternative runtimes), switch and continue.
	if docker --context default info >/dev/null 2>&1; then
		echo "Switching Docker context to default..."
		docker context use default >/dev/null
		return 0
	fi

	# macOS helper: try launching Docker Desktop and wait for daemon readiness.
	if [[ "$(uname -s)" == "Darwin" ]]; then
		echo "Starting Docker Desktop..."
		open -a Docker || true

		for i in {1..60}; do
			if docker info >/dev/null 2>&1; then
				echo "Docker daemon is ready."
				return 0
			fi
			sleep 2
			if (( i % 10 == 0 )); then
				echo "Waiting for Docker daemon... (${i}/60)"
			fi
		done
	fi

	cat <<'EOF'
Unable to connect to Docker daemon.

Try one of these and run ./start.sh again:
1) Start Docker Desktop and wait until it shows "Engine running".
2) If using Colima:
	 colima start
	 docker context use default
EOF
	return 1
}

ensure_docker_running

# Open the frontend and backend API in the default browser on macOS while containers start
open "http://localhost:3000" || true
open "http://localhost:8000" || true

docker compose up --build
