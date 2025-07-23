# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TP_NFC is an NFC-based attendance tracking system for event management. It tracks guest attendance at multiple stations using NFC wristbands and synchronizes data with Google Sheets.

## Architecture

The application follows a layered MVC-like architecture:

- **Presentation Layer**: `src/gui/app.py` - Monolithic CustomTkinter GUI with 3000+ lines
- **Service Layer**: Services in `src/services/` handle NFC, Google Sheets, and tag management
- **Data Layer**: Models in `src/models/` with JSON persistence in `config/`

Key architectural decisions:
- Cross-platform NFC abstraction that auto-selects backend (nfcpy vs pyscard)
- Asynchronous operations using ThreadPoolExecutor for non-blocking UI
- Offline-first design with local queue that syncs when connection available
- Thread-safe UI updates using `safe_update_widget` wrapper

## Common Commands

```bash
# Install dependencies (use platform-specific scripts)
./install.command  # macOS
./install.bat      # Windows

# Run the application
./start.command    # macOS
./start.bat        # Windows

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
```

## Key Components

1. **NFC Service** (`src/services/unified_nfc_service.py`): Abstracts NFC reader interaction with automatic backend selection based on platform
2. **Google Sheets Service** (`src/services/google_sheets_service.py`): Manages attendance data synchronization with retry logic
3. **Tag Manager** (`src/services/tag_manager.py`): Handles NFC tag-to-guest mappings with local persistence
4. **Check-in Queue** (`src/services/check_in_queue.py`): Implements offline queue with background sync
5. **Main GUI** (`src/gui/app.py`): Complex state management with multiple operational modes

## Important Configuration

- `config/config.json` - Main application settings
- `config/credentials.json` - Google API credentials (not in repo)
- `config/tag_registry.json` - NFC tag mappings (auto-generated)
- `config/check_in_queue.json` - Offline queue persistence

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

See `Improvements.yaml` for detailed improvement plan focusing on:
- State management refactoring
- Resource cleanup improvements
- Performance optimizations
- Error handling enhancements

The project is actively being stabilized with focus on reliability for live event usage.