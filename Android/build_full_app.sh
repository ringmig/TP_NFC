#!/bin/bash
# Build script for full TP_NFC Android app

echo "🔨 Building Full TP_NFC Android App"
echo "=================================="

# Check if buildozer is installed
if ! command -v buildozer &> /dev/null; then
    echo "❌ Error: buildozer not found. Please install it with:"
    echo "pip install buildozer"
    exit 1
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf .buildozer/android/app/main.py*
rm -rf bin/*.apk

# Backup default buildozer.spec and use the full spec
echo "🔄 Setting up configuration..."
if [ -f "buildozer.spec" ]; then
    cp buildozer.spec buildozer_test_backup.spec
fi
cp buildozer_full.spec buildozer.spec

# Build the app
echo "🏗️  Starting build process (this may take 10-20 minutes)..."
echo "Using full TP_NFC configuration"
buildozer android debug

# Restore original buildozer.spec
echo "🔄 Restoring original configuration..."
if [ -f "buildozer_test_backup.spec" ]; then
    mv buildozer_test_backup.spec buildozer.spec
fi

# Check if build was successful
if ls bin/*.apk 1> /dev/null 2>&1; then
    echo "✅ Build completed successfully!"
    echo "APK location: $(ls bin/*.apk)"
    echo ""
    echo "To install the app, run:"
    echo "cd android_studio_project && ./install_apk.sh full"
else
    echo "❌ Build failed. Check the logs above for errors."
    exit 1
fi