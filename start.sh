#!/bin/bash

# Run from repo root
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "🚀 Starting Vireon Agentic CFO Stack..."

# Open the frontend and backend API in the default browser on macOS while containers start
open "http://localhost:3000" || true
open "http://localhost:8000" || true

docker compose up --build
