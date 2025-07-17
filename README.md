# TP_NFC - NFC Attendance Tracking System

## Overview

A cross-platform NFC attendance tracking system that uses NTAG213 wristbands and Google Sheets for real-time attendance management.

## Features

- **NFC Wristband Registration**: Link NTAG213 wristbands to guest IDs
- **Real-time Google Sheets Integration**: Live updates to attendance spreadsheet
- **Multi-station Support**: Track attendance at multiple checkpoints
- **Cross-platform**: Works on Windows and macOS
- **Simple GUI**: Easy-to-use interface for FOH staff

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- USB NFC Reader (ACR122U, SCL3711, or similar)
- NTAG213 wristbands
- Google account with access to your attendance spreadsheet

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/ringmig/TP_NFC.git
   cd TP_NFC
   ```

2. Run the installation script:
   
   **Windows:**
   ```
   install.bat
   ```
   
   **macOS:**
   - First time only: Open Terminal and run:
     ```
     cd /path/to/TP_NFC
     chmod +x *.command
     ```
   - Then double-click `install.command`
   
   This will set up a virtual environment and install all required dependencies.

### Configuration

1. **Google Sheets Setup**:
   - Follow the guide in `GOOGLE_SHEETS_SETUP.md`
   - Add your spreadsheet ID to `config/config.json`
   - Download credentials and save as `config/credentials.json`

2. **NFC Reader**:
   - Connect your USB NFC reader
   - No additional configuration needed for supported readers

### Running the Application

To start the application:

**Windows:**
- Double-click `start.bat`

**macOS:**
- Double-click `start.command`

### Testing Tools

**Test NFC Reader:**
- Windows: `tools\test_nfc.bat`
- macOS: `tools/test_nfc.command`

**Test Google Sheets Connection:**
- Windows: `tools\test_sheets.bat`
- macOS: `tools/test_sheets.command`

**Diagnose NFC Issues:**
- Windows: `tools\diagnose_nfc.bat`
- macOS: `tools/diagnose_nfc.command`

## Usage

### Registering Wristbands

1. FOH staff looks up guest in Google Sheet
2. Enters guest's original ID in the application
3. Taps wristband on reader to register

### Checkpoint Scanning

1. Select the current station
2. Guests tap their wristband
3. Attendance is automatically marked in Google Sheets

## Project Structure

```
TP_NFC/
├── src/                      # Source code
│   ├── main.py              # Main application entry
│   ├── models/              # Data models
│   │   ├── nfc_tag.py      # NFC tag model
│   │   └── guest_record.py  # Guest record model
│   ├── services/            # Business logic
│   │   ├── nfc_service.py   # NFC operations
│   │   ├── google_sheets_service.py  # Google Sheets API
│   │   └── tag_manager.py   # Tag-guest coordination
│   └── utils/               # Utilities
│       ├── logger.py        # Logging setup
│       └── helpers.py       # Helper functions
├── config/                  # Configuration files
│   └── config.json         # App configuration
├── logs/                    # Application logs
├── tests/                   # Unit tests
└── requirements.txt         # Python dependencies
```

## Supported Hardware

### NFC Readers
- ACR122U (recommended)
- SCL3711
- PN532 USB module
- Any PC/SC compatible reader

### NFC Tags
- NTAG213 wristbands (required)
- 180 bytes user memory
- ISO 14443A compatible

## Troubleshooting

### NFC Reader Issues
- Ensure reader is connected via USB
- Check that no other NFC software is running
- On Windows: May need to install drivers
- On macOS: May need to install libusb via Homebrew

### Google Sheets Issues
- Verify spreadsheet ID is correct
- Ensure credentials.json is in config/ folder
- Check that you've enabled Google Sheets API
- Confirm you're added as a test user in OAuth consent

## Configuration

All settings are in `config/config.json`:
- Google Sheets credentials and spreadsheet ID
- Station names
- NFC reader timeout
- UI preferences

## Security

- Google credentials are stored locally
- Tag registry is saved in `config/tag_registry.json`
- No sensitive data is stored on NFC tags
- All logs are local only

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License.