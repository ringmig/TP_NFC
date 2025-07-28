#!/bin/bash
# Build minimal working version with Python 3.11

echo "🔨 Building Minimal TP_NFC Android App with Python 3.11"
echo "======================================================="

# Activate Python 3.11 virtual environment
source buildozer_env_311/bin/activate

echo "✅ Using Python: $(which python)"
echo "✅ Python version: $(python --version)"

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf .buildozer/android/app/main.py*
rm -rf bin/*.apk

# Backup current files
echo "📝 Setting up minimal version..."
cp main.py main_backup.py 2>/dev/null || true
cp buildozer.spec buildozer_backup.spec 2>/dev/null || true

# Use minimal files
cp main_minimal.py main.py
cp buildozer_minimal_working.spec buildozer.spec

# Build with Python 3.11
echo "🏗️  Building minimal version..."
buildozer android debug

# Restore files
echo "🔄 Restoring original files..."
if [ -f "main_backup.py" ]; then
    mv main_backup.py main.py
else
    echo "No backup found for main.py"
fi
if [ -f "buildozer_backup.spec" ]; then
    mv buildozer_backup.spec buildozer.spec
else
    echo "No backup found for buildozer.spec"
fi

# Check if build was successful
if ls bin/*.apk 1> /dev/null 2>&1; then
    echo "✅ Minimal build completed successfully!"
    echo "APK location: $(ls bin/*.apk)"
    echo ""
    echo "To install the app, run:"
    echo "cd android_studio_project && ./install_apk.sh full"
else
    echo "❌ Build failed. Check the logs above for errors."
    deactivate
    exit 1
fi

deactivate