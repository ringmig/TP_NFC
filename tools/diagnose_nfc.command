#!/bin/bash
# Diagnose NFC reader issues on macOS

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "NFC Reader Diagnostic"
echo "===================="
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

# Install pyusb if not already installed
echo "Ensuring pyusb is installed..."
pip install pyusb > /dev/null 2>&1

# Run the diagnostic
python tools/diagnose_nfc.py

echo ""
echo "Press any key to close..."
read -n 1 -s