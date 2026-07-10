#!/usr/bin/env bash
# Launches the Flask backend on http://localhost:${PORT:-5000}. Requires venv/ to exist
# (see README "How to Use"). Set PORT to override, e.g. PORT=5051 ./scripts/run_server.sh
# if 5000 is already taken (macOS AirPlay Receiver commonly squats on it).
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -d venv ]; then
    echo "venv/ not found — run: python3.12 -m venv venv && source venv/bin/activate && pip install -r requirements-dev.txt" >&2
    exit 1
fi

exec venv/bin/python3 -m server
