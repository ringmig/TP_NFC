# TP_NFC Android Studio Project

This project provides Android Studio integration for the TP_NFC Kivy-based Android application.

## Project Structure

- `../apk/test_01.apk` - Pre-built APK from buildozer
- `install_apk.sh` - Script to install APK for testing
- `app/` - Android Studio project for development/debugging

## Quick Start

### Option 1: Install Existing APK (Recommended for Testing)

1. **Connect Android device or start emulator**
2. **Run installation script:**
   ```bash
   ./install_apk.sh
   ```
3. **Launch app from device or use ADB:**
   ```bash
   adb shell am start -n org.example.testapp/org.kivy.android.PythonActivity
   ```

### Option 2: Android Studio Development

1. **Open this project in Android Studio:**
   - File → Open → Select `android_studio_project` folder
   
2. **For APK testing:**
   - Use "External Tools" to run `install_apk.sh`
   - Debug via ADB logcat
   
3. **For native development:**
   - Modify `app/` module 
   - Add Chaquopy integration for Python code

## APK Information

- **Package**: `org.example.testapp`
- **Main Activity**: `org.kivy.android.PythonActivity` (Kivy-generated)
- **Architecture**: arm64-v8a, armeabi-v7a
- **Python Version**: 3.11
- **Framework**: Kivy + KivyMD

## Development Workflow

1. **Python Changes**: Modify files in `../src/` and rebuild APK with buildozer
2. **Android Changes**: Modify native Android code in `app/` module
3. **Testing**: Use `install_apk.sh` for quick testing cycles

## Debugging

- **Python logs**: `adb logcat | grep python`
- **Kivy logs**: `adb logcat | grep kivy`
- **General logs**: `adb logcat | grep testapp`

## Build Commands

```bash
# From ../Android directory:
buildozer android debug          # Build debug APK
buildozer android release        # Build release APK
buildozer android clean          # Clean build files
```