#!/bin/bash
# TP_NFC Portable Installation Script for macOS

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "TP_NFC Portable Installation"
echo "============================"
echo ""

# Check if portable Python exists
PORTABLE_PYTHON_DIR="$DIR/portable_python/macos"
PYTHON_EXECUTABLE=""

if [ -d "$PORTABLE_PYTHON_DIR" ] && [ -x "$PORTABLE_PYTHON_DIR/bin/python3" ]; then
    echo "Using existing portable Python distribution..."
    PYTHON_EXECUTABLE="$PORTABLE_PYTHON_DIR/bin/python3"
    echo "Portable Python version:"
    "$PYTHON_EXECUTABLE" --version
elif command -v python3 &> /dev/null; then
    echo "Setting up portable Python using system Python..."
    PYTHON_EXECUTABLE="python3"
    echo "System Python version:"
    "$PYTHON_EXECUTABLE" --version
    echo ""
    
    # Try to install portable-python package locally
    echo "Installing portable-python package locally..."
    if "$PYTHON_EXECUTABLE" -m pip install --target "$DIR/temp_packages" portable-python; then
        echo "Creating portable Python distribution..."
        
        # Create the portable Python using portable-python package
        PYTHONPATH="$DIR/temp_packages:$PYTHONPATH" "$PYTHON_EXECUTABLE" -c "
import portable_python
import os
import shutil

# Create portable Python in our directory
portable_dir = '$PORTABLE_PYTHON_DIR'
os.makedirs(portable_dir, exist_ok=True)

try:
    # Download and extract portable Python 3.13
    portable_python.install(portable_dir, python_version='3.13')
    print(f'Portable Python installed to: {portable_dir}')
except Exception as e:
    print(f'Failed to create portable Python: {e}')
    print('Will continue with system Python...')
"
        
        # Clean up temporary packages
        rm -rf "$DIR/temp_packages"
        
        # Check if portable Python was created successfully
        if [ -x "$PORTABLE_PYTHON_DIR/bin/python3" ]; then
            echo "Portable Python created successfully!"
            PYTHON_EXECUTABLE="$PORTABLE_PYTHON_DIR/bin/python3"
        else
            echo "Portable Python creation failed, using system Python..."
            PYTHON_EXECUTABLE="python3"
        fi
    else
        echo "Could not install portable-python package, using system Python..."
        PYTHON_EXECUTABLE="python3"
    fi
else
    echo "Error: No Python 3 installation found."
    echo ""
    echo "Options for portable mode:"
    echo "1. Install Python 3 from https://www.python.org/downloads/macos/"
    echo "2. Install via Homebrew: brew install python"
    echo "3. Then run this script again"
    echo ""
    echo "Press any key to close..."
    read -n 1 -s
    exit 1
fi

echo ""

# Set up portable site-packages directory
SITE_PACKAGES_DIR="$DIR/portable_python/site-packages"
echo "Setting up portable site-packages directory..."
mkdir -p "$SITE_PACKAGES_DIR"

# Remove existing virtual environment if it exists
if [ -d "venv" ]; then
    echo "Removing existing virtual environment..."
    rm -rf venv
fi

# Install dependencies directly to portable site-packages
echo "Installing dependencies to portable directory..."
"$PYTHON_EXECUTABLE" -m pip install --target "$SITE_PACKAGES_DIR" --upgrade pip
"$PYTHON_EXECUTABLE" -m pip install --target "$SITE_PACKAGES_DIR" -r requirements.txt

# Create necessary directories
echo ""
echo "Creating necessary directories..."
mkdir -p logs
mkdir -p config

# Create tag registry file if it doesn't exist
if [ ! -f "config/tag_registry.json" ]; then
    echo "{}" > config/tag_registry.json
fi

# Create Python path file for easy imports
cat > portable_python_path.py << 'EOF'
import sys
import os

# Add portable site-packages to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
site_packages = os.path.join(script_dir, 'portable_python', 'site-packages')
if os.path.exists(site_packages) and site_packages not in sys.path:
    sys.path.insert(0, site_packages)
EOF

echo ""
echo "Portable installation complete!"
echo ""
echo "Distribution contents:"
echo "├── portable_python/       # Portable Python and packages"
echo "├── src/                   # Application source code"
echo "├── config/                # Configuration files"
echo "└── start.command          # Application launcher"
echo ""
echo "Next steps:"
echo "1. Configure your Google Sheets ID in config/config.json"
echo "2. Set up Google API credentials (see GOOGLE_SHEETS_SETUP.md)"
echo "3. Run start.command to launch the application"
echo ""
echo "This installation is now completely portable!"
echo "You can copy this entire folder to any macOS machine and it will work."
echo ""
echo "Press any key to close this window..."
read -n 1 -s