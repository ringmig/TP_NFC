#!/bin/bash
# Push Python files directly to Android emulator for instant testing

echo "📱 Push to Android Studio Emulator (Kivy Launcher Method)"
echo "========================================================"

# Check if emulator is running
if ! adb devices | grep -q "emulator.*device"; then
    echo "❌ No Android emulator detected. Please start one in Android Studio."
    exit 1
fi

echo "✅ Android emulator detected: $(adb devices | grep emulator | cut -f1)"

# Create project directory on emulator
PROJECT_DIR="/sdcard/kivy/tpnfc"
echo "📁 Creating project directory on emulator..."
adb shell mkdir -p "$PROJECT_DIR"

# Push main Python file
echo "📤 Pushing main.py to emulator..."
adb push main.py "$PROJECT_DIR/"

# Create a simple main.py launcher for Kivy Launcher
echo "📝 Creating Kivy Launcher compatible main.py..."
cat > temp_launcher.py << 'EOF'
#!/usr/bin/env python3
# Kivy Launcher compatible version

import kivy
kivy.require('2.1.0')

# Import the main app
from main import TPNFCApp

if __name__ == '__main__':
    TPNFCApp().run()
EOF

# Push launcher
adb push temp_launcher.py "$PROJECT_DIR/main.py"
rm temp_launcher.py

# Push any assets if they exist
if [ -d "assets" ]; then
    echo "📤 Pushing assets..."
    adb push assets/ "$PROJECT_DIR/"
fi

echo "🎯 Files pushed to emulator!"
echo ""
echo "📋 Next steps:"
echo "1. Install 'Kivy Launcher' from Google Play Store on your emulator"
echo "2. Open Kivy Launcher app"
echo "3. Navigate to 'tpnfc' project"
echo "4. Tap to run instantly!"
echo ""
echo "💡 For development:"
echo "   - Edit main.py locally"
echo "   - Run this script to update emulator"
echo "   - Refresh in Kivy Launcher to see changes"
echo ""
echo "📱 Emulator path: $PROJECT_DIR"