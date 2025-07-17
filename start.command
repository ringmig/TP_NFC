#!/bin/bash
# TP_NFC Application Launcher for macOS

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "Starting TP_NFC Attendance System..."
echo "===================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found."
    echo "Please run install.command first."
    echo ""
    echo "Press any key to close..."
    read -n 1 -s
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if main.py exists
if [ ! -f "src/main.py" ]; then
    echo "Error: src/main.py not found."
    echo "Please ensure you're in the correct directory."
    echo ""
    echo "Press any key to close..."
    read -n 1 -s
    exit 1
fi

# Run the application
python src/main.py

# Keep window open if there's an error
if [ $? -ne 0 ]; then
    echo ""
    echo "Application exited with an error."
    echo "Press any key to close..."
    read -n 1 -s
fi