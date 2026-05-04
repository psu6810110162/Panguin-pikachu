# Penguin Dash - Setup Instructions

## Environment Setup (macOS - Apple Silicon)

### Initial Setup (One Time)
```bash
# Create virtual environment with Python 3.12
/opt/homebrew/bin/python3.12 -m venv venv

# Activate venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install kivy pillow pygame
```

### Running the Game
```bash
# Navigate to project directory
cd "/Users/aphchat/Coding Year 1/KIVY_Project/Panguin-pikachu"

# Activate venv
source venv/bin/activate

# Run the game
python main.py
```

## System Requirements
- **Python**: 3.12.13 (via Homebrew)
- **Kivy**: 2.3.1+
- **Platform**: macOS (Apple Silicon/ARM64)

## Troubleshooting

### Environment not working?
```bash
# Deactivate current venv
deactivate

# Remove old venv
rm -rf venv

# Recreate venv
/opt/homebrew/bin/python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install kivy pillow pygame
```

### Why Python 3.12?
- Python 3.13/3.14 have a known `pyexpat` compatibility issue on macOS Tahoe (Apple Silicon)
- Python 3.12 is stable, fully tested, and works perfectly with Kivy
- You can upgrade later when the issue is fixed upstream

## Notes
- Ensure Xcode Command Line Tools are updated: `xcode-select --install`
- Kivy requires binary wheels on Apple Silicon (avoid source compilation)
