#!/bin/bash
# Fast development build and install to Android Studio emulator

echo "🔨 Fast Dev Build for Android Studio Emulator"
echo "============================================="

# Check if emulator is running
if ! adb devices | grep -q "emulator.*device"; then
    echo "❌ No Android emulator detected. Please start one in Android Studio."
    exit 1
fi

echo "✅ Android emulator detected"

# Use the working Python 3.12 virtual environment if it exists
if [ -d "buildozer_env" ]; then
    echo "📦 Using existing buildozer environment..."
    source buildozer_env/bin/activate
elif command -v python3.12 &> /dev/null; then
    echo "📦 Using Python 3.12..."
    # Create quick virtual env
    python3.12 -m venv dev_env
    source dev_env/bin/activate
    pip install buildozer cython setuptools
else
    echo "📦 Using system Python..."
fi

# Clean previous builds for faster iteration
echo "🧹 Quick clean..."
rm -rf bin/*.apk

# Create simple buildozer config for fast builds
echo "⚙️  Creating fast build config..."
cat > buildozer_dev.spec << 'EOF'
[app]
title = TP NFC Dev
package.name = tpnfcdev
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3,kivy==2.1.0
orientation = portrait
fullscreen = 0

[buildozer]
log_level = 1
build_dir = ./.buildozer
bin_dir = ./bin

[android]
android.api = 30
android.minapi = 21
android.ndk = 25b
android.sdk = 30
android.build_tools = 30.0.3
android.archs = armeabi-v7a
android.permissions = INTERNET,ACCESS_NETWORK_STATE,NFC
android.theme = "@android:style/Theme.NoTitleBar"
android.release_artifact = apk
android.debug_artifact = apk
android.enable_androidx = True
EOF

# Try to build (this might still fail locally, but worth trying)
echo "🏗️  Attempting local build..."
if buildozer -v android debug; then
    echo "✅ Local build successful!"
    
    # Install to emulator
    APK_FILE=$(find bin -name "*.apk" -type f | head -1)
    if [ -n "$APK_FILE" ]; then
        echo "📱 Installing to emulator..."
        adb uninstall org.example.tpnfcdev 2>/dev/null || true
        adb install "$APK_FILE"
        
        echo "🚀 Launching app..."
        adb shell am start -n org.example.tpnfcdev/org.kivy.android.PythonActivity
        
        echo "✅ App installed and launched on emulator!"
        echo "💡 Edit main.py and run this script again for quick iteration"
    else
        echo "❌ APK not found after build"
    fi
else
    echo "❌ Local build failed (expected - use GitHub Actions for reliable builds)"
    echo ""
    echo "💡 Alternative: Use desktop development with 'python3 main.py'"
    echo "   Then push to GitHub when ready for mobile testing"
fi

# Cleanup
if [ -f "buildozer_dev.spec" ]; then
    rm buildozer_dev.spec
fi