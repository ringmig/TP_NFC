#!/bin/bash
# TP_NFC Portable Installation Script for macOS (Updated)
# Matches Windows portable distribution approach

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "TP_NFC Portable Installation (Updated)"
echo "======================================"
echo ""

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 not found."
    echo ""
    echo "Please install Python 3:"
    echo "1. Download from https://www.python.org/downloads/macos/"
    echo "2. Or install via Homebrew: brew install python"
    echo "3. Then run this script again"
    echo ""
    echo "Press any key to close..."
    read -n 1 -s
    exit 1
fi

echo "Found Python 3:"
python3 --version
echo ""

# Set up portable site-packages directory (using new /python structure)
SITE_PACKAGES_DIR="$DIR/python/site-packages"
echo "Setting up portable site-packages directory..."
mkdir -p "$SITE_PACKAGES_DIR"

# Remove existing virtual environment if it exists
if [ -d "venv" ]; then
    echo "Removing existing virtual environment..."
    rm -rf venv
fi

# Install dependencies to local site-packages (matches Windows --target approach)
echo "Installing/upgrading pip..."
python3 -m pip install --target "$SITE_PACKAGES_DIR" --upgrade pip

echo "Installing dependencies to portable directory..."
if [ -f "requirements.txt" ]; then
    python3 -m pip install --target "$SITE_PACKAGES_DIR" -r requirements.txt
    if [ $? -eq 0 ]; then
        echo "Successfully installed packages from requirements.txt."
    else
        echo "ERROR: Failed to install requirements from requirements.txt"
        echo "Please check the requirements.txt file and your internet connection."
        echo "Press any key to close..."
        read -n 1 -s
        exit 1
    fi
else
    echo "No requirements.txt found, skipping dependency installation."
fi

# Create necessary directories
echo ""
echo "Creating application directories..."
mkdir -p logs
mkdir -p config

# Create tag registry file if it doesn't exist
if [ ! -f "config/tag_registry.json" ]; then
    echo "{}" > config/tag_registry.json
    echo "Created default config/tag_registry.json"
fi

echo ""
echo "Setup complete!"
echo "Portable site-packages directory: $SITE_PACKAGES_DIR"
echo ""
echo "Distribution structure:"
echo "├── python/site-packages/           # All Python packages"
echo "├── src/                            # Application source code"
echo "├── config/                         # Configuration files"
echo "└── launchers/start_updated.command # Application launcher"
echo ""
echo "Next steps:"
echo "1. Configure your Google Sheets ID in config/config.json"
echo "2. Set up Google API credentials (see GOOGLE_SHEETS_SETUP.md)"
echo "3. Run launchers/start_updated.command to launch the application"
echo ""
echo "This installation is now portable!"
echo "Copy this entire folder to any macOS machine and it will work."
echo ""
echo "Press any key to close..."
read -n 1 -s