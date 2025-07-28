#!/bin/bash
# Build APK using the same approach as the working GitHub Actions workflow

echo "🔨 Building TP_NFC Android App (GitHub Actions way)"
echo "=================================================="

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf bin/*.apk
rm -rf .buildozer/android/app/main.py*

# Backup original files
echo "📝 Backing up original files..."
cp buildozer.spec buildozer_original.spec 2>/dev/null || true

# Prepare buildozer.spec with the exact settings from GitHub workflow
echo "🔧 Configuring buildozer.spec with working settings..."
cat > buildozer.spec << 'EOF'
[app]
title = TP NFC
package.name = testapp
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3,kivy==2.1.0
orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2
build_dir = ./.buildozer
bin_dir = ./bin

[android]
android.api = 30
android.minapi = 21
android.ndk = 25b
android.sdk = 30
android.build_tools = 30.0.3
android.archs = armeabi-v7a
android.permissions = INTERNET,ACCESS_NETWORK_STATE,NFC,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.theme = "@android:style/Theme.NoTitleBar"
android.release_artifact = apk
android.debug_artifact = apk
android.enable_androidx = True
p4a.branch = develop
EOF

# Create a simple test main.py first to ensure build works
echo "📝 Creating simple test app..."
cp main.py main_backup.py 2>/dev/null || true
cat > main.py << 'EOF'
#!/usr/bin/env python3

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout

class TestApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=50, spacing=20)
        
        title = Label(
            text='TP_NFC Android',
            font_size='24sp',
            size_hint_y=None,
            height='60dp'
        )
        
        status = Label(
            text='Test Build\n\nUsing GitHub Actions configuration',
            font_size='16sp',
            halign='center'
        )
        status.bind(size=status.setter('text_size'))
        
        layout.add_widget(title)
        layout.add_widget(status)
        
        return layout

if __name__ == '__main__':
    TestApp().run()
EOF

# Install specific versions that work in GitHub Actions
echo "📦 Installing specific package versions..."
pip3 install --user cython==0.29.33 buildozer==1.5.0

# Try building with regular buildozer
echo "🏗️  Building APK..."
buildozer android debug

# Check if build was successful
if ls bin/*.apk 1> /dev/null 2>&1; then
    echo "✅ Build completed successfully!"
    echo "APK location: $(ls bin/*.apk)"
    echo ""
    echo "To install the app, run:"
    echo "cd android_studio_project && ./install_apk.sh full"
else
    echo "❌ Build failed. Check the logs above for errors."
    echo ""
    echo "Note: The GitHub workflow uses Docker with pre-installed Android SDK."
    echo "For local builds without Docker, you may need to:"
    echo "1. Install Android SDK manually"
    echo "2. Set up proper environment variables"
    echo "3. Accept Android licenses"
fi

# Restore original files
echo "🔄 Restoring original files..."
if [ -f "main_backup.py" ]; then
    mv main_backup.py main.py
fi
if [ -f "buildozer_original.spec" ]; then
    mv buildozer_original.spec buildozer.spec
fi