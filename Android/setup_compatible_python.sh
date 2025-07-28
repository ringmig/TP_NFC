#!/bin/bash
# Setup compatible Python for Android development

echo "🐍 Setting up Python 3.12 for Android development"
echo "================================================="

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew not found. Please install Homebrew first:"
    echo "https://brew.sh"
    exit 1
fi

# Install Python 3.12
echo "📦 Installing Python 3.12..."
brew install python@3.12

# Check if installation was successful
if command -v python3.12 &> /dev/null; then
    echo "✅ Python 3.12 installed successfully!"
    echo "Version: $(python3.12 --version)"
    
    # Install buildozer with Python 3.12
    echo "📦 Installing buildozer with Python 3.12..."
    python3.12 -m pip install --user buildozer
    
    # Create wrapper script for buildozer
    cat > buildozer_py312 << 'EOF'
#!/bin/bash
# Buildozer wrapper using Python 3.12
export PYTHON_FOR_BUILD="/opt/homebrew/bin/python3.12"
/opt/homebrew/bin/python3.12 -m buildozer "$@"
EOF
    chmod +x buildozer_py312
    
    echo "✅ Setup complete!"
    echo ""
    echo "To build with Python 3.12, use:"
    echo "./buildozer_py312 android debug"
    echo ""
    echo "Or update your build scripts to use python3.12"
    
else
    echo "❌ Failed to install Python 3.12"
    echo "Please try manually: brew install python@3.12"
    exit 1
fi