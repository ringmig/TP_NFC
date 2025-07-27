# TP_NFC - NFC Attendance Tracking System

A professional cross-platform NFC attendance tracking system that uses NTAG213 wristbands and Google Sheets for real-time attendance management at events and venues.

## Table of Contents

- [Features](#features)
- [Project Status](#project-status)
- [Getting Started](#getting-started)
- [Google Sheets Setup](#google-sheets-setup)
- [Configuration](#configuration)
- [Usage](#usage)
- [Architecture](#architecture)
- [Hardware Support](#hardware-support)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Contributing](#contributing)

## Features

### ✅ Complete Core System
- **NFC Wristband Registration**: Link NTAG213 wristbands to guest IDs with auto-check-in
- **Real-time Google Sheets Integration**: Live bidirectional sync with attendance spreadsheet
- **Multi-station Support**: Track attendance at multiple checkpoints (Reception, Lio, Juntos, etc.)
- **Cross-platform**: Windows, macOS, and Linux support with automatic NFC backend selection
- **Professional GUI**: Modern CustomTkinter interface with light/dark themes

### ✅ Advanced Features
- **Offline-First Design**: Local queue system with background sync for reliable operation
- **Smart Guest Management**: Multi-word search, real-time filtering, editable check-in times
- **Dynamic Station Detection**: Auto-detects new stations from Google Sheets headers
- **Comprehensive Tag Operations**: Write, rewrite, erase, and info display for NFC tags
- **Visual Feedback**: Real-time status updates, countdown timers, and progress indicators
- **Data Integrity**: Sync conflict resolution and automatic backup systems

### ✅ User Experience
- **Modern Interface**: Clean design with outline+hover button patterns
- **Theme Support**: Seamless light/dark mode switching with persistence
- **Keyboard Shortcuts**: Cmd/Ctrl+R (refresh), Cmd/Ctrl+F (search), F11 (fullscreen)
- **Smart Operations**: Auto-clear timers, hover tooltips, and intelligent state management
- **Robust Error Handling**: Graceful degradation and user-friendly error messages

## Project Status

This is a complete, production-ready NFC attendance system with **3000+ lines of code** across multiple components:

### Core Infrastructure ✅
- Project structure with proper separation of concerns
- Cross-platform support (Windows, macOS, Linux)  
- Comprehensive logging system with file and console output
- Configuration management with hot-reload capabilities
- Thread pool executor for non-blocking background operations

### NFC Integration ✅
- Unified NFC service with automatic backend selection (nfcpy/pyscard)
- Support for multiple readers (ACR122U, SCL3711, PN532, PC/SC compatible)
- NTAG213 tag reading/writing with proper error handling
- Tag registry system with backup and recovery
- Optimized timing (3-5 second loops for responsiveness)

### Google Sheets Integration ✅  
- OAuth2 authentication with token management
- Dynamic station detection from spreadsheet headers
- Batch operations and rate limiting compliance
- Guest data caching for offline operation
- Automatic refresh on internet connection restore

### Modern GUI Application ✅
- **Complete Theme System**: Light/dark mode toggle with full UI theming
- **Advanced TreeView**: Borderless design, hover effects, summary rows
- **Smart State Management**: Operation locks, background scanning, mode transitions
- **Tooltip System**: Phone number display with proper timer management
- **Interactive Elements**: All buttons use modern outline+hover pattern
- **Non-Interactive Protection**: Summary rows and headers excluded from interactions

### Production Features ✅
- **Background Scanning**: Continuous NFC monitoring in checkpoint mode
- **Manual Check-in**: Direct guest ID entry with station selection
- **Tag Info Display**: Instant guest information from scanned tags
- **Data Management**: Clear operations, log viewer, advanced developer tools
- **Real-time Monitoring**: Internet connectivity detection and sync status

## Getting Started

### Prerequisites

- **Git** for cloning the repository
- **USB NFC Reader** (ACR122U recommended)
- **NTAG213 Wristbands** for guest identification
- **Google Account** with Sheets access

> **Note**: Python and all dependencies are included! No external Python installation required.

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ringmig/TP_NFC.git
   cd TP_NFC
   ```

2. **Run the one-time setup:**
   
   **Windows:**
   ```cmd
   install.bat
   ```
   
   **macOS/Linux:**
   ```bash
   chmod +x *.command
   ./install.command
   ```
   
   This installs portable Python and all dependencies locally within the project folder.

3. **Connect your NFC reader** via USB

4. **Set up Google Sheets** (see detailed setup below)

### Quick Start

**Run the application:**
- **Windows**: Double-click `launchers/start.bat`
- **macOS/Linux**: Double-click `launchers/start.command` (recommended for cleanest experience)

**For development:**
- Use `python3 run.py` in VS Code or terminal

**Test your setup:**
- NFC Reader: `tools/test_nfc.command`
- Google Sheets: `tools/test_sheets.command`
- Full Diagnostics: `tools/diagnose_nfc.command`

## Google Sheets Setup

### Step 1: Prepare Your Spreadsheet

Your Google Sheet should have these columns:

| Column | Header | Description |
|--------|--------|-------------|
| A | originalid | Unique guest ID (number) |
| B | firstname | Guest's first name |
| C | lastname | Guest's last name |
| D | mobilenumber | Phone number (optional) |
| E+ | station_name | Check-in columns (e.g., reception, lio, juntos) |

**Example:**
```
originalid | firstname | lastname | mobilenumber | reception | lio | juntos
1001       | John      | Doe      | +1234567890  |           |     |
1002       | Jane      | Smith    | +0987654321  |           |     |
```

### Step 2: Get Your Spreadsheet ID

1. Open your Google Sheet
2. Copy the ID from the URL: `https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID/edit`
3. Update `config/config.json`:
   ```json
   {
     "google_sheets": {
       "spreadsheet_id": "paste-your-id-here"
     }
   }
   ```

### Step 3: Enable Google Sheets API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable the **Google Sheets API**
4. Create OAuth2 credentials:
   - Application type: **Desktop app**
   - Download the JSON file
   - Save as `config/credentials.json`

### Step 4: Configure OAuth Consent

1. Configure OAuth consent screen (External)
2. Add your email as a test user
3. Set app status to "Testing"

### Step 5: Test Connection

Run `tools/test_sheets.command` - it will:
1. Open browser for Google authentication
2. Generate `config/token.json` for future use
3. Verify spreadsheet access

## Configuration

All settings are stored in `config/config.json`:

### UI Settings

```json
{
  "ui": {
    "window_mode": "maximized",        // "normal", "maximized", "fullscreen"
    "window_width": 1200,              // Used in normal mode
    "window_height": 800,              // Used in normal mode
    "window_title": "TP NFC Attendance",
    "theme": "dark"                    // "light" or "dark"
  }
}
```

**Window Modes:**
- **`maximized`** (default): Fills screen, keeps dock/taskbar
- **`fullscreen`**: True fullscreen (macOS/Linux only)  
- **`normal`**: Standard resizable window

### Google Sheets Settings

```json
{
  "google_sheets": {
    "spreadsheet_id": "your-spreadsheet-id",
    "sheet_name": "Sheet1",            // Tab name in your spreadsheet
    "credentials_file": "config/credentials.json",
    "token_file": "config/token.json",
    "scopes": ["https://www.googleapis.com/auth/spreadsheets"]
  }
}
```

### NFC Settings

```json
{
  "nfc": {
    "timeout": 5,                      // Tag detection timeout (seconds)
    "retry_attempts": 3,               // Connection retry attempts
    "backend": "auto"                  // "auto", "nfcpy", or "pyscard"
  }
}
```

### Station Configuration

```json
{
  "stations": ["Station 1", "Station 2", "Station 3", "Station 4", "Station 5"]
}
```

**Note:** Stations are now auto-detected from your spreadsheet headers. This setting serves as fallback.

### Keyboard Shortcuts

- **F11** - Toggle fullscreen mode
- **Cmd/Ctrl+R** - Refresh guest data
- **Cmd/Ctrl+F** - Focus search field
- **ESC** - Close dialogs/return to previous state

## Usage

### Registration Workflow (Reception Station)

1. **Enter Guest ID**: Staff looks up guest in spreadsheet and enters their original ID
2. **Scan Wristband**: Guest taps NTAG213 wristband on NFC reader
3. **Auto Check-in**: Guest is automatically checked in at Reception
4. **Visual Confirmation**: Success message displays guest name

### Checkpoint Scanning (All Stations)

1. **Select Station**: Click station button (Reception, Lio, Juntos, etc.)
2. **Continuous Scanning**: Application monitors for wristband taps
3. **Instant Updates**: Check-ins sync immediately to Google Sheets
4. **Visual Feedback**: Guest name and timestamp displayed

### Advanced Operations

**Settings Panel**:
- **Tag Info**: Scan wristband to display guest information
- **Rewrite Tag**: Change which guest a wristband is assigned to  
- **Erase Tag**: Remove guest assignment from wristband
- **View Logs**: Application log viewer with auto-refresh
- **Advanced**: Data management and diagnostics (password protected)

**Manual Check-in**:
- Enable manual mode with orange "Manual Check-in" button
- Click on guest rows to check them in without NFC scanning
- Automatically exits after successful check-in

**Search & Filter**:
- Type in search box to filter guest list
- Supports multi-word search (order independent)
- Real-time filtering as you type

## Architecture

### Project Structure

```
TP_NFC/
├── src/                             # Source code
│   ├── main.py                     # Application entry point
│   ├── gui/
│   │   └── app.py                  # Main GUI (3000+ lines)
│   ├── models/
│   │   ├── guest_record.py         # Guest data model
│   │   └── nfc_tag.py             # NFC tag model
│   ├── services/
│   │   ├── unified_nfc_service.py  # Auto-selecting NFC backend
│   │   ├── google_sheets_service.py # Google Sheets integration
│   │   ├── tag_manager.py          # Tag-guest coordination
│   │   └── check_in_queue.py       # Offline sync queue
│   └── utils/
│       ├── logger.py               # Logging configuration
│       └── helpers.py              # Utility functions
├── config/                         # Configuration files
│   ├── config.json                # Main application settings
│   ├── credentials.json           # Google API credentials (not in git)
│   ├── token.json                 # OAuth tokens (not in git)
│   ├── tag_registry.json          # NFC tag mappings (not in git)
│   ├── check_in_queue.json        # Offline queue (not in git)
│   └── guest_cache.json           # Cached guest data (not in git)
├── logs/                          # Application logs
├── tools/                         # Testing and diagnostic tools
└── requirements.txt               # Python dependencies
```

### Key Design Patterns

**Thread Safety:**
- UI updates via `self.after()` scheduling
- Background operations in ThreadPoolExecutor
- Proper widget lifecycle management

**State Management:**
- Operation flags prevent concurrent operations
- Mode transitions with proper cleanup
- Background scanning with cancellation support

**Offline-First:**
- Local queue for check-ins during network outages
- Cached guest data for offline operation
- Automatic sync when connection restored

**Error Resilience:**
- Comprehensive exception handling
- Graceful degradation when services unavailable
- User-friendly error messages and recovery guidance

## Hardware Support

### NFC Readers

**Recommended:**
- **ACR122U** - Most tested, excellent compatibility
- **SCL3711** - Reliable alternative
- **PN532 USB** - Budget-friendly option

**Requirements:**
- PC/SC compatible
- USB connection
- ISO 14443A support

**Platform Notes:**
- **Windows**: May require driver installation
- **macOS**: Built-in drivers, libusb via Homebrew if needed
- **Linux**: Requires pcscd service running

### NFC Tags

**Supported:**
- **NTAG213** (required) - 180 bytes user memory
- ISO 14443A Type 2 compatible
- 13.56 MHz frequency

**Wristband Options:**
- Silicone wristbands with embedded NTAG213
- Adjustable sizing for comfort
- Waterproof for event environments

## Troubleshooting

### NFC Reader Issues

**Reader not detected:**
```bash
# Test NFC connectivity
./tools/test_nfc.command

# Check for driver issues
./tools/diagnose_nfc.command
```

**Common solutions:**
- Ensure no other NFC software is running
- Try different USB port
- Restart NFC service: `sudo systemctl restart pcscd` (Linux)
- Install/update drivers from `Resources/NFC Reader Driver/`

### Google Sheets Issues

**Authentication errors:**
```bash
# Test Sheets connection
./tools/test_sheets.command
```

**Common solutions:**
- Verify `spreadsheet_id` in config.json
- Ensure `credentials.json` exists in config/
- Check OAuth consent screen has your email as test user
- Delete `token.json` to force re-authentication

**"No data found":**
- Verify column headers match expected format
- Check sheet name in config (default: "Sheet1")
- Ensure spreadsheet is accessible to your Google account

### Application Issues

**Won't start:**
- Check Python version: `python --version` (need 3.9+)
- Reinstall dependencies: `./install.command`
- Check logs in `logs/TP_NFC.log`

**Performance issues:**
- Reduce NFC timeout in config.json
- Clear old log files
- Check for conflicting NFC applications

**Data sync issues:**
- Check internet connectivity
- View pending operations in Advanced settings
- Use "Refresh Guest List" to force sync

## Development

### State Management

The application uses a sophisticated state management system documented in the codebase:

**Core States:**
- `operation_in_progress` - Blocks concurrent operations
- `is_scanning` - Controls background NFC scanning
- `settings_visible` - Settings panel overlay state
- `is_rewrite_mode` - Rewrite tag mode isolation

**Threading Patterns:**
- Main UI thread for all widget updates
- Background ThreadPoolExecutor for NFC/API operations
- Proper cleanup and cancellation support

**Mode Transitions:**
- Reception: Registration + Checkpoint modes
- Other Stations: Checkpoint-only scanning
- Settings: Overlay with state restoration
- Rewrite: Isolated mode with forced return to Reception

### Key Components

**NFCService** (`unified_nfc_service.py`):
- Auto-selects backend (nfcpy vs pyscard)
- Handles timeouts and error recovery
- Thread-safe operation patterns

**GoogleSheetsService** (`google_sheets_service.py`):
- OAuth2 authentication management
- Dynamic station detection
- Batch operations with retry logic
- Offline caching and sync

**TagManager** (`tag_manager.py`):
- Coordinates NFC and Sheets operations
- Manages tag-to-guest registry
- Handles check-in queue and conflicts

### Testing

**Manual Testing Tools:**
```bash
# Test individual components
./tools/test_nfc.command       # NFC reader functionality
./tools/test_sheets.command    # Google Sheets API
./tools/diagnose_nfc.command   # Comprehensive NFC diagnostics

# Stress testing
python tools/test_concurrent_nfc.py  # Concurrent operations
```

**Unit Tests:**
```bash
# Run test suite
pytest

# With coverage
pytest --cov
```

### Code Quality

**Linting:**
```bash
flake8 src/
```

**Type Checking:**
```bash
mypy src/
```

**Security Scanning:**
```bash
bandit -r src/
safety check
```

## Contributing

1. **Fork the repository**
2. **Create a feature branch:** `git checkout -b feature/amazing-feature`
3. **Follow the coding standards:**
   - Use type hints
   - Add docstrings for public methods
   - Follow PEP 8 style guide
   - Test your changes
4. **Commit your changes:** `git commit -m 'Add amazing feature'`
5. **Push to the branch:** `git push origin feature/amazing-feature`
6. **Open a Pull Request**

### Development Setup

```bash
# Clone and setup development environment
git clone https://github.com/ringmig/TP_NFC.git
cd TP_NFC
./install.command

# Install development dependencies
pip install -r requirements-dev.txt

# Run in development mode
python src/main.py
```

### Code Organization

- **Keep UI logic in `app.py`** - All interface components and state management
- **Business logic in `services/`** - Separate concerns for NFC, Sheets, etc.
- **Data models in `models/`** - Clean data structures without business logic
- **Utilities in `utils/`** - Shared helper functions and configuration

### Pull Request Guidelines

- Include comprehensive tests for new features
- Update documentation for user-facing changes
- Ensure backward compatibility for configuration files
- Test on multiple platforms when possible
- Include screenshots for UI changes

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/ringmig/TP_NFC/issues)
- **Documentation**: This README and inline code comments
- **Hardware**: Refer to `Resources/` directory for NFC reader setup

---

**Built with ♥ for seamless event management**