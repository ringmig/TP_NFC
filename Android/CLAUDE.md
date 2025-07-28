# CLAUDE.md - Android Development

This file provides guidance to Claude Code when working with the TP_NFC Android project.

## STRICT OPERATIONAL PROTOCOL:

**BOOTSTRAP SEQUENCE:**
   - First: Read this Android/CLAUDE.md to load Android-specific context
   - Second: Review root CLAUDE.md for overall project context
   - Third: Check current build status and active configurations

**STATE SYNCHRONIZATION:**
   - After Android changes: Update this Android/CLAUDE.md
   - Keep updates concise but complete with current build status

## Current Session Summary (Android Studio Integration & Build Fixes)

### ✅ Completed This Session:

**1. Android Studio Project Setup** (FULLY WORKING ✅):
- **Created Android Studio project structure** in `android_studio_project/`
- **Proper Gradle configuration** with Chaquopy for Python integration
- **Fixed repository conflicts** in build.gradle and settings.gradle
- **APK installation workflow** with automatic ADB detection from Android Studio SDK
- **Debug logging scripts** for development workflow

**2. APK Testing & Analysis** (FULLY WORKING ✅):
- **Existing APK working**: `apk/test_01.apk` (35MB, "Hello World" test app)
- **Successful installation**: Package `org.example.testapp` with activity `org.kivy.android.PythonActivity`
- **App running correctly** on Android device/emulator
- **ADB integration**: Scripts auto-detect ADB from `~/Library/Android/sdk/platform-tools/`

**3. Build System Configuration** (IN PROGRESS 🔄):
- **Identified Python 3.13 compatibility issue**: `jnius` errors with `long` type
- **Root cause**: buildozer/python-for-android not fully compatible with Python 3.13
- **Solution created**: Python 3.12 compatibility layer with dedicated build scripts

**Key Technical Solutions**:
- **ADB Path Resolution**: Auto-detect Android Studio SDK ADB location
- **Package Management**: Support both test and full app installations
- **Build Environment**: Created Python 3.12 compatibility scripts
- **Activity Detection**: Proper Android activity naming (`org.kivy.android.PythonActivity`)

## Project Structure

```
Android/
├── android_studio_project/          # Android Studio integration
│   ├── app/                         # Main Android Studio module  
│   │   ├── build.gradle            # Chaquopy + dependencies
│   │   ├── src/main/
│   │   │   ├── AndroidManifest.xml # NFC + permissions
│   │   │   ├── java/com/tp/nfc/    # Native Android code
│   │   │   ├── python/             # Python source files
│   │   │   └── res/                # Android resources
│   │   └── ...
│   ├── build.gradle                # Project-level config
│   ├── settings.gradle             # Repository settings
│   ├── install_apk.sh              # APK installation script
│   ├── debug_logs.sh               # Debug logging script
│   └── README.md                   # Setup instructions
├── apk/
│   └── test_01.apk                 # Working test APK (35MB)
├── src/                            # Android Python source
├── main.py                         # Current: Full TP_NFC app
├── main_***.py                     # Various app versions
├── buildozer*.spec                 # Build configurations
├── build_*.sh                      # Build scripts
├── setup_compatible_python.sh     # Python 3.12 setup
└── CLAUDE.md                       # This file
```

## Current Build Status

### ✅ **Working Components:**
- **Test APK**: Simple "Hello World" app successfully running
- **Android Studio Integration**: Project opens and syncs correctly
- **APK Installation**: Automated installation and launch scripts
- **Debug Workflow**: Logging and development tools

### 🔄 **In Progress:**
- **Full TP_NFC Build**: Python 3.13 compatibility blocking build
- **Python 3.12 Setup**: Solution scripts created, needs execution

### ❌ **Known Issues:**
- **Python 3.13 + buildozer**: `jnius` compile errors (`long` type undefined)
- **CMake compatibility**: Version conflicts in build dependencies

## Build Configurations

### **Current Active Configuration:**
- **Main app**: `main.py` (full TP_NFC app - switched from test version)
- **Build spec**: `buildozer_full.spec` (TP NFC with all features)
- **Python version**: 3.13 (causing build issues)

### **Available Build Scripts:**
1. **`build_full_app.sh`** - Full featured app (blocked by Python 3.13)
2. **`build_simple.sh`** - Minimal working version (blocked by Python 3.13)  
3. **`build_with_py312.sh`** - Python 3.12 compatibility build ⭐ **RECOMMENDED**
4. **`setup_compatible_python.sh`** - Install Python 3.12 environment ⭐ **REQUIRED FIRST**

### **APK Management:**
- **Test APK**: `./install_apk.sh` (installs test_01.apk)
- **Full APK**: `./install_apk.sh full` (installs from bin/ directory)

## Immediate Next Steps

### **Priority 1: Resolve Build Issues**
```bash
# 1. Install Python 3.12 for compatibility
./setup_compatible_python.sh

# 2. Build with Python 3.12
./build_with_py312.sh

# 3. Install new APK
cd android_studio_project && ./install_apk.sh full
```

### **Priority 2: Feature Development**
Once building works:
1. Add NFC functionality gradually
2. Integrate Google Sheets API
3. Add full TP_NFC features
4. Test on real hardware

## Development Workflow

### **Android Studio Development:**
1. **Open project**: `android_studio_project/` in Android Studio
2. **Install APK**: Use `install_apk.sh` for testing
3. **Debug**: Use `debug_logs.sh` for real-time logging
4. **Native development**: Modify Java code in `app/src/main/java/`

### **Python Development:**
1. **Modify**: Python code in `src/` or `main*.py`
2. **Build**: Use appropriate `build_*.sh` script
3. **Test**: Install and test new APK
4. **Iterate**: Debug and improve

### **Common Commands:**
```bash
# Install Python 3.12 and buildozer
./setup_compatible_python.sh

# Build full app with Python 3.12
./build_with_py312.sh

# Install test APK
cd android_studio_project && ./install_apk.sh

# Install full APK (after successful build)
cd android_studio_project && ./install_apk.sh full

# View debug logs
cd android_studio_project && ./debug_logs.sh

# Check running apps
$HOME/Library/Android/sdk/platform-tools/adb shell dumpsys activity activities | grep tpnfc
```

## Key Technical Details

### **Android Package Information:**
- **Test App**: `org.example.testapp` (simple "Hello World")
- **Full App**: `com.ringmig.tpnfc.tpnfc` (complete TP_NFC features)
- **Main Activity**: `org.kivy.android.PythonActivity` (Kivy-generated)

### **Build Dependencies:**
- **Python**: 3.12 (required for buildozer compatibility)
- **Buildozer**: Latest version with Python 3.12
- **Android SDK**: API 31, NDK 25b
- **Architecture**: arm64-v8a (primary), armeabi-v7a (fallback)

### **Permissions Required:**
- `INTERNET` - Google Sheets API
- `ACCESS_NETWORK_STATE` - Connectivity detection  
- `NFC` - NFC tag reading
- `WRITE_EXTERNAL_STORAGE` - Local data storage
- `READ_EXTERNAL_STORAGE` - Local data access

## Integration with Main Project

This Android project is part of the larger TP_NFC system:
- **Desktop app**: `../src/gui/app.py` (4200+ lines CustomTkinter)
- **Shared services**: Ported to `src/services/` for Android
- **Data models**: Common between desktop and Android
- **Configuration**: Android-specific in `buildozer*.spec`

The goal is feature parity between desktop and Android versions with appropriate platform adaptations.

## Troubleshooting

### **Common Build Issues:**
1. **Python 3.13 errors**: Use `build_with_py312.sh` instead
2. **ADB not found**: Scripts auto-detect from Android Studio SDK
3. **CMake errors**: Usually resolved by Python 3.12 setup
4. **Missing APK**: Check `bin/` directory after successful build

### **Runtime Issues:**
1. **App won't launch**: Check package name in `install_apk.sh`
2. **Black screen**: Use `debug_logs.sh` to see Python errors
3. **Permission denied**: Ensure Android device has developer options enabled

The Android development is well-structured and ready for the next phase once the Python compatibility issue is resolved.