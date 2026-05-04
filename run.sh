#!/bin/bash
# Penguin Dash Game Launcher

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to project directory
cd "$SCRIPT_DIR"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating..."
    /opt/homebrew/bin/python3.12 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install/update dependencies if needed
pip install -q --upgrade pip kivy pillow pygame

# Run the game
echo "Launching Penguin Dash..."
python main.py
