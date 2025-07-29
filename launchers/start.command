#!/bin/bash
# TP_NFC Application Launcher - Updated Portable Version (matches Windows approach)

# Get the directory where this script is located (launchers folder)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Get the project root (TP_NFC folder) - parent of launchers
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

# Change to the project root directory
cd "$PROJECT_DIR"

# Define paths relative to project root (updated for new /python structure)
SITE_PACKAGES_DIR="python/site-packages"
MAIN_SCRIPT="src/main.py"

# Check if site-packages directory exists
if [ ! -d "$SITE_PACKAGES_DIR" ]; then
    echo "Error: Portable site-packages not found at $SITE_PACKAGES_DIR"
    echo "Please run install_updated.command first to set up the environment."
    echo "Press any key to close..."
    read -n 1 -s
    exit 1
fi

# Check if main.py exists
if [ ! -f "$MAIN_SCRIPT" ]; then
    echo "Error: $MAIN_SCRIPT not found."
    echo "Please ensure you are running this from the correct location."
    echo "Press any key to close..."
    read -n 1 -s
    exit 1
fi

# Set PYTHONPATH to include our portable site-packages and src directory
export PYTHONPATH="$PROJECT_DIR/$SITE_PACKAGES_DIR:$PROJECT_DIR/src:$PYTHONPATH"

echo "Running TP_NFC application..."
echo "Current directory: $PROJECT_DIR"
echo "Python packages: $SITE_PACKAGES_DIR"

# Launch the app completely in background using nohup (clean user experience)
nohup python3 "$MAIN_SCRIPT" > /dev/null 2>&1 &

# Exit immediately so terminal closes
exit 0