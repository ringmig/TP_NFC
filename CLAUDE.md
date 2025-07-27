# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## STRICT OPERATIONAL PROTOCOL:

**BOOTSTRAP SEQUENCE:**
   - First: Read CLAUDE.md to load project context and previous session state
   - Second: Review any files mentioned in CLAUDE.md before proceeding
   

**STATE SYNCHRONIZATION:**
   - After code changes: Update this CLAUDE.md.
   - Keep updates concise but complete

**BOOTSTRAP HANDOFF:**
   - Final CLAUDE.md must enable next session to continue seamlessly
   - Include specific method names, line numbers, and error states
   - Document any locks, flags, or states that were in progress
   - Prioritize tracing your steps, documenting what the last edit was.  

## Project Context
**Project:** TP_NFC - NFC attendance tracking system with GUI  
**Location:** `/Users/howard/Documents/GitHub/TP_NFC/`  
**Key Files:** To read before attempting to implement improvements!
- `README.md` - Comprehensive project documentation with setup, configuration, architecture, and development guidelines
- `src/gui/app.py` - Main GUI application (4200+ lines, CustomTkinter)

# Important Configuration

**Desktop Configuration:**
- `config/config.json` - Main application settings
- `config/credentials.json` - Google API credentials (not in repo)
- `config/tag_registry.json` - NFC tag mappings (auto-generated)
- `config/check_in_queue.json` - Offline queue persistence

**Android Configuration:**
- `Android/buildozer.spec` - Android build configuration (API 30, NDK 25b)
- `.github/workflows/android-build.yml` - Automated APK build pipeline
- `Android/requirements.txt` - Python dependencies for mobile app


## Last Session Summary (Portable Distribution System)

### ✅ Completed This Session:

**13. Complete Portable Distribution System** (FULLY WORKING ✅):
- **Windows Portable Python**: Embedded Python 3.13.5 installed locally in `portable_python/windows/`
- **macOS Portable Setup**: Uses system Python 3.13 with all dependencies in local `portable_python/site-packages/`
- **Self-Contained Project**: All dependencies now included within project folder - no external dependencies needed
- **Multiple Launchers**: Clean launcher options in `launchers/` folder for different user preferences
- **Developer Tools**: Simple `python3 run.py` command for VS Code development

**Key Technical Implementation**:
- **Portable Python Path Management**: `portable_python_path.py` automatically configures Python paths
- **Local Dependency Installation**: Updated `install.command`/`install.bat` to install packages locally using `--target`
- **Clean Launcher System**: `start.command` provides optimal user experience (28 lines, nohup approach)
- **Cross-Platform Compatibility**: Windows uses embedded Python, macOS uses system Python with local packages

**Distribution Benefits**:
- **Zero External Dependencies**: Everything needed is included in the project folder
- **Easy Deployment**: Copy entire folder to any machine and run
- **No Virtual Environment Needed**: Portable packages replace venv requirement
- **Clean User Experience**: Double-click launchers work seamlessly

### Previous Major Achievements:
- Complete modern button design system with outline + hover fill pattern
- Light/dark theme toggle with full TreeView theming
- Row hover system with selection elimination  
- NFC status blinking alerts
- Offline data caching with auto-refresh
- Non-interactive UI elements (summary row, headers, tooltips)

## Project Overview

TP_NFC is an NFC-based attendance tracking system for event management. It tracks guest attendance at multiple stations using NFC wristbands and synchronizes data with Google Sheets.

**Platform Support:**
- ✅ **Desktop**: Complete CustomTkinter application (Windows/macOS/Linux)
- ✅ **Android**: Complete KivyMD mobile app with automated APK builds
- 🔄 **Next**: iOS support planned

## Architecture

**Desktop Application (Complete ✅):**
- **Presentation Layer**: `src/gui/app.py` - CustomTkinter GUI with 3000+ lines
- **Service Layer**: Services in `src/services/` handle NFC, Google Sheets, and tag management
- **Data Layer**: Models in `src/models/` with JSON persistence in `config/`

**Android Application (Complete ✅):**
- **Presentation Layer**: `Android/src/gui/` - KivyMD Material Design interface
- **Service Layer**: `Android/src/services/` - Ported from desktop with Android NFC integration
- **Data Layer**: `Android/src/models/` - Same data models as desktop
- **Build System**: Docker-based buildozer with automated GitHub Actions APK generation

Key architectural decisions:
- Cross-platform NFC abstraction that auto-selects backend (nfcpy vs pyscard)
- Asynchronous operations using ThreadPoolExecutor for non-blocking UI
- Offline-first design with local queue that syncs when connection available
- Thread-safe UI updates using `safe_update_widget` wrapper

## Common Commands

```bash
# Setup portable distribution (one-time setup)
./install.command  # macOS - installs all dependencies locally
./install.bat      # Windows - installs all dependencies locally

# Run the application (for end users)
./launchers/start.command  # macOS - recommended, cleanest experience
./launchers/start.bat      # Windows

# Run the application (for development)
python3 run.py                    # Simple launcher for VS Code/development

# Run tests
pytest

# Run tests with coverage
pytest --cov

# Lint code
flake8

# Test NFC reader
./tools/test_nfc.command    # macOS
./tools/test_nfc.bat        # Windows

# Test Google Sheets connection
./tools/test_sheets.command # macOS
./tools/test_sheets.bat     # Windows

# Build Android APK (automated via GitHub Actions)
git add . && git commit -m "Update Android app" && git push origin master
# APK will be available as artifact in GitHub Actions
```

## Key Components

**Desktop Application:**
1. **NFC Service** (`src/services/unified_nfc_service.py`): Abstracts NFC reader interaction with automatic backend selection
2. **Google Sheets Service** (`src/services/google_sheets_service.py`): Manages attendance data synchronization with retry logic
3. **Tag Manager** (`src/services/tag_manager.py`): Handles NFC tag-to-guest mappings with local persistence
4. **Check-in Queue** (`src/services/check_in_queue.py`): Implements offline queue with background sync
5. **Main GUI** (`src/gui/app.py`): Complex state management with multiple operational modes

**Android Application:**
1. **Android NFC Service** (`Android/src/services/android_nfc_service.py`): Native Android NFC integration via pyjnius
2. **Mobile GUI** (`Android/src/gui/screens/main_screen.py`): KivyMD Material Design interface
3. **Shared Services**: Google Sheets, Tag Manager, and Check-in Queue ported from desktop
4. **Build System** (`.github/workflows/android-build.yml`): Docker-based buildozer with automated APK generation

#
## Development Guidelines

1. **State Management**: The GUI uses complex state tracking. Always use `self.operation_in_progress` flag and proper cleanup
2. **Thread Safety**: All UI updates must go through `safe_update_widget()` when called from background threads
3. **Error Handling**: Use comprehensive try-except blocks with user-friendly error messages
4. **NFC Operations**: Always check `nfc_service.is_ready()` before operations
5. **Google Sheets**: Handle offline scenarios gracefully with queue fallback

## Testing Approach

- Manual testing scripts in `/tools` directory for hardware integration
- Unit tests focus on service layer logic
- No automated GUI testing currently implemented

## Known Issues and Improvements
-

The project is actively being stabilized with focus on reliability for live event usage.