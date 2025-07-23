# TP_NFC Android

Android port of the TP_NFC attendance tracking system.

## Features

- **Mobile NFC Reading**: Uses Android's built-in NFC capabilities
- **Portrait UI**: Optimized for mobile device screens
- **Same Core Logic**: Reuses all business logic from desktop version
- **Google Sheets Integration**: Same synchronization system
- **Offline Support**: Local backup and queue system

## Requirements

- Android 6.0+ (API level 23+)
- NFC-enabled device
- Internet connection for Google Sheets sync

## Development Setup

### Prerequisites

1. **Python 3.8+** with pip
2. **Android SDK** (if building locally)
3. **Buildozer** dependencies

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Google Sheets

Copy your Google Sheets credentials to:
```
Android/src/config/credentials.json
```

### Build APK

```bash
# Debug build
buildozer android debug

# Release build  
buildozer android release
```

## Project Structure

```
Android/
├── main.py                 # Entry point
├── buildozer.spec         # Build configuration
├── src/
│   ├── gui/
│   │   ├── screens/       # Mobile UI screens
│   │   └── components/    # Reusable components
│   ├── services/          # Core services (ported from desktop)
│   ├── models/            # Data models (same as desktop)
│   └── utils/             # Android utilities
├── assets/                # App assets
└── requirements.txt       # Python dependencies
```

## Architecture

### UI Framework
- **KivyMD**: Material Design components for Android
- **Portrait-first**: Optimized for mobile use
- **Touch-friendly**: Large buttons and intuitive gestures

### NFC Integration
- **plyer**: Cross-platform NFC access
- **pyjnius**: Direct Android API access
- **Intent handling**: Proper Android NFC integration

### Core Services
- **Google Sheets Service**: Identical to desktop
- **Tag Manager**: Same business logic
- **Check-in Queue**: Offline-first with sync

## Usage

1. **Station Selection**: Use top menu to select current station
2. **Registration Mode**: Enter guest ID and tap NFC tag to register
3. **Check-in Mode**: Simply tap registered NFC tags for check-in
4. **Settings**: Access via top-right gear icon

## Build Configuration

Key settings in `buildozer.spec`:

- **Permissions**: NFC, Internet, Storage access
- **Orientation**: Portrait mode
- **API Level**: Android 33 (Android 13)
- **Dependencies**: All required Python packages

## Testing

### Desktop Testing
Run on desktop for development:
```bash
python main.py
```

### Device Testing
Install debug APK:
```bash
buildozer android debug
adb install bin/tpnfc-*-debug.apk
```

## Deployment

1. Build release APK with signing key
2. Test on multiple Android devices
3. Upload to Google Play Store or distribute directly

## Differences from Desktop

### UI Adaptations
- **Vertical layout**: Stacked components for portrait screens
- **Touch targets**: Larger buttons for finger interaction
- **Navigation**: Drawer menu instead of button bar
- **Cards**: Material Design card layout

### Platform Features
- **Android NFC**: Uses device's built-in NFC reader
- **Notifications**: Android system notifications
- **File system**: Android app storage paths
- **Permissions**: Android runtime permissions

### Performance
- **Startup time**: Optimized for mobile launch
- **Memory usage**: Efficient for mobile constraints
- **Battery**: NFC scanning optimizations