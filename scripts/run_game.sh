#!/usr/bin/env bash
# Launches the Kivy game. Requires venv/ to exist (see README "How to Use").
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -d venv ]; then
    echo "venv/ not found — run: python3.12 -m venv venv && source venv/bin/activate && pip install -r requirements-dev.txt" >&2
    exit 1
fi

exec venv/bin/python3 main.py
