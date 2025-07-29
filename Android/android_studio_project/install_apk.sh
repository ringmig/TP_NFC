#!/bin/bash
# Script to install the TP_NFC APK for testing
# Usage: 
#   ./install_apk.sh           - Install test APK (default)
#   ./install_apk.sh enhanced  - Install enhanced features APK from bin/
#   ./install_apk.sh full      - Install full app APK from bin/

# Check for APK argument or use default
if [ "$1" == "enhanced" ] || [ "$1" == "production" ]; then
    # Use production APK from bin directory
    APK_PATH="../bin/tpnfcenhanced-2.0-arm64-v8a_armeabi-v7a-debug.apk"
    if [ ! -f "$APK_PATH" ]; then
        echo "❌ Production APK not found at $APK_PATH"
        exit 1
    fi
    PACKAGE_NAME="com.tpnfc.tpnfcenhanced"
    ACTIVITY_NAME="org.kivy.android.PythonActivity"
elif [ "$1" == "full" ]; then
    # Look for other full app APKs in bin directory
    APK_PATH=$(ls ../bin/*-debug.apk 2>/dev/null | grep -v "tpnfcenhanced" | head -1)
    if [ -z "$APK_PATH" ]; then
        echo "❌ Full app APK not found. Run build_full_app.sh first."
        exit 1
    fi
    PACKAGE_NAME="com.ringmig.tpnfc.tpnfc"
    ACTIVITY_NAME="org.kivy.android.PythonActivity"
else
    # Use test APK (default)
    APK_PATH="../apk/test_01.apk"
    PACKAGE_NAME="org.example.testapp"
    ACTIVITY_NAME="org.kivy.android.PythonActivity"
fi

echo "📱 Installing APK: $(basename "$APK_PATH")"

# Try to find ADB in common locations
if command -v adb &> /dev/null; then
    ADB="adb"
elif [ -f "$HOME/Library/Android/sdk/platform-tools/adb" ]; then
    ADB="$HOME/Library/Android/sdk/platform-tools/adb"
else
    echo "Error: ADB not found. Please install Android SDK Platform Tools."
    echo "You can add it to PATH by running:"
    echo "echo 'export PATH=\"\$HOME/Library/Android/sdk/platform-tools:\$PATH\"' >> ~/.zshrc"
    echo "source ~/.zshrc"
    exit 1
fi

echo "Installing TP_NFC APK..."
echo "Using ADB at: $ADB"

# Check if device/emulator is connected
if ! $ADB devices | grep -q "device$"; then
    echo "Error: No Android device or emulator connected."
    echo "Please connect a device or start an emulator."
    exit 1
fi

# Uninstall previous version if exists
echo "Uninstalling previous version..."
$ADB uninstall $PACKAGE_NAME 2>/dev/null || true

# Install the APK
echo "Installing APK..."
if $ADB install "$APK_PATH"; then
    echo "✅ APK installed successfully!"
    echo "Package: $PACKAGE_NAME"
    echo "You can now run the app from Android Studio or launch it manually on the device."
    
    # Optionally launch the app
    echo "Launching TP_NFC app..."
    $ADB shell am start -n $PACKAGE_NAME/$ACTIVITY_NAME
else
    echo "❌ Failed to install APK"
    exit 1
fi