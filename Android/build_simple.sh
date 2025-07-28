#!/bin/bash
# Build script for a working simple version first

echo "🔨 Building Simple Working TP_NFC Android App"
echo "=============================================="

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf .buildozer/android/app/main.py*
rm -rf bin/*.apk

# Create a simple working main.py temporarily
echo "📝 Creating simple working version..."
cp main.py main_full_backup.py
cat > main.py << 'EOF'
#!/usr/bin/env python3

from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen

class SimpleTPApp(MDApp):
    def build(self):
        screen = MDScreen()
        label = MDLabel(
            text="TP_NFC Simple Test\n\nThis proves the build system works!\n\nNext: Add full features",
            halign="center",
            theme_text_color="Primary"
        )
        screen.add_widget(label)
        return screen

if __name__ == '__main__':
    SimpleTPApp().run()
EOF

# Use minimal spec
echo "🔄 Using minimal buildozer configuration..."
cp buildozer.spec buildozer_backup.spec
cat > buildozer.spec << 'EOF'
[app]
title = TP NFC Simple
package.name = tpnfcsimple
package.domain = com.ringmig.tpnfc
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0.0
requirements = python3,kivy==2.1.0,kivymd
orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2
build_dir = ./.buildozer
bin_dir = ./bin

[android]
android.api = 31
android.minapi = 21
android.ndk = 25b
android.sdk = 31
android.archs = arm64-v8a
p4a.branch = develop
android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.theme = "@android:style/Theme.NoTitleBar"
android.release_artifact = apk
android.debug_artifact = apk
android.enable_androidx = True
EOF

# Build the app
echo "🏗️  Building simple version (should be faster)..."
buildozer android debug

# Restore files
echo "🔄 Restoring original files..."
if [ -f "main_full_backup.py" ]; then
    mv main_full_backup.py main.py
fi
if [ -f "buildozer_backup.spec" ]; then
    mv buildozer_backup.spec buildozer.spec
fi

# Check if build was successful
if ls bin/*.apk 1> /dev/null 2>&1; then
    echo "✅ Simple build completed successfully!"
    echo "APK location: $(ls bin/*.apk)"
    echo ""
    echo "To install the simple app, run:"
    echo "cd android_studio_project && ./install_apk.sh full"
    echo ""
    echo "If this works, we can then add more features gradually."
else
    echo "❌ Build failed. Check the logs above for errors."
    exit 1
fi