#!/bin/bash
# TP_NFC Android App Launcher (Desktop Testing)

# Get the directory where this script is located (Android folder)
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "Starting TP_NFC Android App (Desktop Mode)..."
echo "Window: 400x700 pixels (mobile portrait simulation)"
echo ""

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo "Error: main.py not found in Android directory"
    echo "Please ensure you are in the correct location."
    echo "Press any key to close..."
    read -n 1 -s
    exit 1
fi

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 not found"
    echo "Please install Python 3 and try again"
    echo "Press any key to close..."
    read -n 1 -s
    exit 1
fi

# Launch the Android app in desktop mode (background with clean exit)
nohup python3 main.py > /dev/null 2>&1 &

# Exit immediately so terminal closes
exit 0