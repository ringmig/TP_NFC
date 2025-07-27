#!/bin/bash
# TP_NFC Installation Script for macOS

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "TP_NFC Installation"
echo "=================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed."
    echo "Please install Python 3 from https://www.python.org/downloads/"
    exit 1
fi

echo "Python version:"
python3 --version
echo ""

# Remove existing virtual environment if it exists
if [ -d "venv" ]; then
    echo "Removing existing virtual environment..."
    rm -rf venv
fi

echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo ""
echo "Creating necessary directories..."
mkdir -p logs
mkdir -p config

# Create tag registry file if it doesn't exist
if [ ! -f "config/tag_registry.json" ]; then
    echo "{}" > config/tag_registry.json
fi

echo ""
echo "Installation complete!"
echo ""
echo "Next steps:"
echo "1. Configure your Google Sheets ID in config/config.json"
echo "2. Set up Google API credentials (see GOOGLE_SHEETS_SETUP.md)"
echo "3. Run start.command to launch the application"
echo ""
echo "Press any key to close this window..."
read -n 1 -s