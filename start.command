#!/bin/bash
# TP_NFC Application Launcher for macOS (Hidden)

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Launch hidden by redirecting output and running in background
{
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        osascript -e 'display notification "Virtual environment not found. Please run install.command first." with title "TP_NFC Error"'
        exit 1
    fi

    # Activate virtual environment
    source venv/bin/activate

    # Check if main.py exists
    if [ ! -f "src/main.py" ]; then
        osascript -e 'display notification "src/main.py not found. Please ensure you are in the correct directory." with title "TP_NFC Error"'
        exit 1
    fi

    # Run the application
    python src/main.py

} > /dev/null 2>&1 &
