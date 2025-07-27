#!/bin/bash
# TP_NFC Application Launcher for macOS (Hidden/Auto-closing)

# Minimize terminal window immediately
osascript -e 'tell application "Terminal" to set miniaturized of front window to true' > /dev/null 2>&1 &

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Function to show error and wait for user input
show_error_and_wait() {
    echo "$1"
    echo ""
    echo "Press any key to close..."
    read -n 1 -s
    exit 1
}

# Function to auto-close terminal (for error cases only)
auto_close_terminal() {
    sleep 0.5
    osascript -e 'tell application "Terminal" to close front window' > /dev/null 2>&1 || exit 0
}

# Suppress normal output for hidden mode (comment out these lines if you want to see startup messages)
exec > /dev/null 2>&1

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    # Re-enable output for error
    exec > /dev/tty 2>&1
    osascript -e 'tell application "Terminal" to set miniaturized of front window to false' > /dev/null 2>&1
    show_error_and_wait "Error: Virtual environment not found. Please run install.command first."
fi

# Activate virtual environment
source venv/bin/activate

# Check if main.py exists
if [ ! -f "src/main.py" ]; then
    # Re-enable output for error
    exec > /dev/tty 2>&1
    osascript -e 'tell application "Terminal" to set miniaturized of front window to false' > /dev/null 2>&1
    show_error_and_wait "Error: src/main.py not found. Please ensure you're in the correct directory."
fi

# Run the application (re-enable output for the main app)
exec > /dev/tty 2>&1

# Optional: Keep terminal hidden while app runs (uncomment if you want completely silent startup)
# exec > /dev/null 2>&1

# Use exec to replace the bash process with Python process
# This prevents the "close running process" dialog when using Cmd+Q
exec python src/main.py