#!/bin/bash
# Complete development workflow for Android Studio

echo "🚀 TP_NFC Development Workflow"
echo "=============================="

echo "Choose your development method:"
echo "1. 💻 Desktop Preview (Fastest - instant feedback)"
echo "2. 📱 Push to Emulator (Kivy Launcher - near instant)"
echo "3. 📦 Local APK Build (Slower but real APK testing)"
echo "4. ☁️  GitHub Actions Build (Production builds)"
echo ""
read -p "Enter choice (1-4): " choice

case $choice in
    1)
        echo "🖥️  Starting desktop preview..."
        python3 main.py
        ;;
    2)
        echo "📱 Pushing to Android Studio emulator..."
        ./push_to_emulator.sh
        ;;
    3)
        echo "📦 Building APK locally..."
        ./dev_build_install.sh
        ;;
    4)
        echo "☁️  Triggering GitHub Actions build..."
        echo "💡 Make sure to commit and push your changes first:"
        echo "   git add ."
        echo "   git commit -m 'UI updates'"
        echo "   git push origin master"
        echo ""
        echo "🔗 Monitor build at: https://github.com/ringmig/TP_NFC/actions"
        ;;
    *)
        echo "❌ Invalid choice"
        ;;
esac