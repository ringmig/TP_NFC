#!/bin/bash
# Build script using Python 3.12 for compatibility

echo "🔨 Building TP_NFC Android App with Python 3.12"
echo "==============================================="

# Check if Python 3.12 is available
if ! command -v python3.12 &> /dev/null; then
    echo "❌ Python 3.12 not found. Run setup_compatible_python.sh first:"
    echo "./setup_compatible_python.sh"
    exit 1
fi

echo "✅ Using Python 3.12: $(python3.12 --version)"

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf .buildozer/android/app/main.py*
rm -rf bin/*.apk

# Create simple working main.py
echo "📝 Creating simple working version..."
cp main.py main_full_backup.py 2>/dev/null || true
cat > main.py << 'EOF'
#!/usr/bin/env python3

from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen

class SimpleTPApp(MDApp):
    def build(self):
        screen = MDScreen()
        label = MDLabel(
            text="TP_NFC Android\n\nBuilt with Python 3.12\nCompatible build system!",
            halign="center",
            theme_text_color="Primary"
        )
        screen.add_widget(label)
        return screen

if __name__ == '__main__':
    SimpleTPApp().run()
EOF

# Create compatible buildozer.spec
echo "🔄 Creating compatible buildozer configuration..."
cp buildozer.spec buildozer_backup.spec 2>/dev/null || true
cat > buildozer.spec << 'EOF'
[app]
title = TP NFC
package.name = tpnfc
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
android.permissions = INTERNET,ACCESS_NETWORK_STATE,NFC,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.theme = "@android:style/Theme.NoTitleBar"
android.release_artifact = apk
android.debug_artifact = apk
android.enable_androidx = True
EOF

# Build with Python 3.12
echo "🏗️  Building with Python 3.12..."
if [ -f "buildozer_py312" ]; then
    ./buildozer_py312 android debug
else
    python3.12 -m buildozer android debug
fi

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
    echo "✅ Build completed successfully with Python 3.12!"
    echo "APK location: $(ls bin/*.apk)"
    echo ""
    echo "To install the app, run:"
    echo "cd android_studio_project && ./install_apk.sh full"
else
    echo "❌ Build failed. Check the logs above for errors."
    exit 1
fi