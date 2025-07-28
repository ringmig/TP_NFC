#!/bin/bash
# Debug logs for TP_NFC Android app

echo "🔍 Starting TP_NFC Android Debug Logs"
echo "Press Ctrl+C to stop"
echo "=================================="

# Try to find ADB in common locations
if command -v adb &> /dev/null; then
    ADB="adb"
elif [ -f "$HOME/Library/Android/sdk/platform-tools/adb" ]; then
    ADB="$HOME/Library/Android/sdk/platform-tools/adb"
else
    echo "Error: ADB not found. Please install Android SDK Platform Tools."
    exit 1
fi

# Check if device/emulator is connected
if ! $ADB devices | grep -q "device$"; then
    echo "Error: No Android device or emulator connected."
    exit 1
fi

# Clear existing logs
$ADB logcat -c

# Start filtered logging
$ADB logcat | grep -E "(python|kivy|testapp|PythonActivity)" --line-buffered