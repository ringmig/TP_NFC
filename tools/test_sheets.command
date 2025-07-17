#!/bin/bash
# Test Google Sheets connectivity on macOS

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "Google Sheets Test"
echo "=================="
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

# Run the sheets test
python tools/test_sheets.py

echo ""
echo "Press any key to close..."
read -n 1 -s