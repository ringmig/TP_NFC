# TP_NFC Project Status

## This is an NFC attendance system with complete GUI and backend services.

**Key Architecture:**
- `src/gui/app.py` - Main GUI (CustomTkinter, 3000+ lines)
- `src/services/` - Business logic (NFC, Google Sheets, Tag Management)
- `src/models/` - Data models (NFCTag, GuestRecord)

**UI Modes:**
- Registration mode (Reception station)
- Checkpoint mode (all stations)
- Settings panel with advanced operations
- Tag info display with auto-close

**NFC Services:**
- Unified backend (nfcpy + pyscard)
- Auto-platform selection (macOS prefers pyscard)
- 3-5 second timeout loops for responsiveness

## Components

### Core Infrastructure 
- [x] Project structure with proper separation of concerns
- [x] Cross-platform support (Windows & macOS)
- [x] Logging system with file and console output
- [x] Configuration management (config.json)
- [x] Configurable window modes (normal/maximized/fullscreen)
- [x] [cite_start]Managed thread pool for background tasks (8 ad-hoc threading.Thread instances replaced) [cite: 2]

### NFC Integration 
- [x] Unified NFC service with automatic backend selection
- [x] Support for multiple NFC readers (ACR122U, SCL3711, etc.)
- [x] NTAG213 tag reading capability
- [x] Tag registry system for ID mapping
- [x] Cross-platform compatibility:
- [x] Windows: nfcpy with libusb
- [x] macOS: pyscard with built-in drivers

### Google Sheets Integration
- [x] OAuth2 authentication
- [x] Guest data fetching
- [x] Attendance marking with timestamps
- [x] Batch update support
- [x] Error handling and logging
- [x] Data clearing capabilities

### Data Models
- [x] NFCTag model for tag management
- [x] GuestRecord model for attendance tracking
- [x] Tag-to-guest mapping system

### GUI Application
- [x] Professional CustomTkinter interface with dark theme
- [x] Configurable window display (normal/maximized/fullscreen)
- [x] Station switching with visual button highlights
- [x] Dynamic content modes (Registration/Checkpoint/Settings)
- [x] Smart guest list with multi-word search (order-independent)
- [x] Real-time status updates with centralized messaging
- [x] Manual check-in capabilities
- [x] Settings panel with reordered advanced operations
- [x] Copyright branding in settings mode
- [x] [cite_start]Memory leak prevention (widget reference cleanup) [cite: 2]
- [x] [cite_start]Safe widget update patterns (safe_update_widget and update_status implementation) [cite: 2]

### Advanced Features
- [x] **Check-in Queue System**: Failsafe local storage with background sync
- [x] **Tag Operations**: Write, erase, rewrite, and info display
- [x] **Sync Conflict Resolution**: Handles offline/online data discrepancies
- [x] **Background Scanning**: Continuous NFC monitoring in checkpoint mode
- [x] **Manual Check-in**: Direct guest ID check-in with station selection
- [x] **Advanced Mode**: Password-protected data clearing functions
- [x] **Log Viewer**: Built-in application log display
- [x] **Tag Info Display**: Inline guest information from scanned tags
- [x] **Smart Search**: Multi-word, order-independent guest filtering
- [x] **Dynamic Station Detection**: Auto-detects new stations from Google Sheets headers
- [x] **Editable Treeview**: Double-click to edit check-in values with immediate feedback
- [x] **Visual Feedback System**: Hourglasses for pending syncs, green rows for complete guests
- [x] **Real-time Internet Monitoring**: Automatic detection of connectivity loss/restoration
- [x] **Fixed Summary Row**: Non-scrollable "checked in / total" counts always visible
- [x] **Auto-Clear Guest ID**: 15-second timeout prevents accidental registrations
- [x] **Offline Protection**: Blocks operations when internet unavailable

### User Experience Enhancements
- [x] **Keyboard Shortcuts**: 
- [x] **Centralized Status Messages**: Consistent mode-aware messaging
- [x] **Visual Feedback**: Real-time countdown timers for operations
- [x] **Smart UI**: Context-aware button visibility and functionality

### Registration Workflow
- [x] ID validation against Google Sheets
- [x] Tag scanning with visual feedback and countdown
- [x] Success/error notifications with guest name display
- [x] Background tag scanning for registration assistance

### Checkpoint Scanning
- [x] Continuous scanning mode for check-ins
- [x] Station-specific scanning with duplicate detection
- [x] Real-time attendance confirmation
- [x] Handling of unregistered tags with clear messaging

### Testing & Tools
- [x] NFC connectivity test
- [x] Google Sheets connectivity test
- [x] NFC diagnostic tool
- [x] Cross-platform launcher scripts

## File Structure
TP_NFC/
├── src/                        # Source code
│   ├── main.py                # Complete entry point
│   ├── models/                # Data models
│   ├── services/              # Business logic
│   │   ├── unified_nfc_service.py     # Auto-selecting NFC backend
│   │   ├── tag_manager.py             # Advanced tag coordination
│   │   ├── google_sheets_service.py   # Complete Sheets integration
│   │   └── check_in_queue.py          # Failsafe sync system
│   ├── gui/                   # Complete GUI
│   │   └── app.py            # Production-ready interface
│   └── utils/                 # Utilities
├── config/                    # Configuration
│   ├── config.json           # Complete configuration
│   ├── config_example.json   # Template
│   └── tag_registry.json     # Persistent tag mappings
├── tools/                     # Testing and diagnostic tools
└── logs/                      # Application logs


## Platform-Specific Files

### Windows
- install.bat, start.bat
- test_nfc.bat, test_sheets.bat, diagnose_nfc.bat

### macOS  
- install.command, start.command
- test_nfc.command, test_sheets.command, diagnose_nfc.command

## Dependencies
All production-ready in requirements.txt:
- NFC: nfcpy, pyusb, pyscard
- Google: google-api-python-client, google-auth
- GUI: customtkinter, Pillow
- Testing: pytest, coverage tools