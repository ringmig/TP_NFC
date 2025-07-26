# Configuration Options

All settings are stored in `config/config.json`. Here's a complete reference:

## UI Settings

### Window Mode (`ui.window_mode`)

Controls how the application window appears when launched:

- **`"maximized"`** (default) - Window fills the screen but keeps title bar and dock/taskbar visible
- **`"fullscreen"`** - True fullscreen mode, hides dock/taskbar (macOS/Linux only, Windows uses maximized)
- **`"normal"`** - Standard window size using `window_width` and `window_height` settings

**Example:**
```json
{
  "ui": {
    "window_mode": "maximized",
    "window_width": 1200,
    "window_height": 800,
    "window_title": "TP NFC Attendance",
    "theme": "dark"
  }
}
```

### Theme Options
- **`theme`** - Color theme: `"light"` or `"dark"` (persistent across sessions)

## Google Sheets Settings

```json
{
  "google_sheets": {
    "spreadsheet_id": "your-spreadsheet-id",
    "sheet_name": "Sheet1",
    "credentials_file": "config/credentials.json",
    "token_file": "config/token.json",
    "scopes": ["https://www.googleapis.com/auth/spreadsheets"]
  }
}
```

## NFC Settings

```json
{
  "nfc": {
    "timeout": 5,
    "retry_attempts": 3,
    "backend": "auto"
  }
}
```

- **`timeout`** - Tag detection timeout in seconds (3-10 recommended)
- **`retry_attempts`** - Connection retry attempts (1-5)
- **`backend`** - NFC backend: `"auto"`, `"nfcpy"`, or `"pyscard"`

## Station Configuration

```json
{
  "stations": ["Reception", "Lio", "Juntos", "Experimental", "Unvrs"]
}
```

**Note:** Stations are auto-detected from your spreadsheet headers. This serves as fallback only.

## Logging Settings

```json
{
  "logging": {
    "level": "INFO",
    "file": "logs/TP_NFC.log",
    "max_size": "10MB",
    "backup_count": 5
  }
}
```

## Keyboard Shortcuts

These are built-in and cannot be changed:

- **F11** - Toggle fullscreen mode
- **Cmd/Ctrl+R** - Refresh guest data
- **Cmd/Ctrl+F** - Focus search field
- **ESC** - Close dialogs/return to previous state

## Advanced Settings

```json
{
  "advanced": {
    "auto_refresh_interval": 300,
    "cache_timeout": 600,
    "sync_batch_size": 50,
    "internet_check_interval": 10
  }
}
```

- **`auto_refresh_interval`** - Seconds between automatic data refreshes (0 = disabled)
- **`cache_timeout`** - Seconds to keep cached data valid
- **`sync_batch_size`** - Maximum items to sync in one batch
- **`internet_check_interval`** - Seconds between connectivity checks

## Example Complete Configuration

```json
{
  "ui": {
    "window_mode": "maximized",
    "window_width": 1200,
    "window_height": 800,
    "window_title": "Event Attendance",
    "theme": "dark"
  },
  "google_sheets": {
    "spreadsheet_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
    "sheet_name": "Sheet1",
    "credentials_file": "config/credentials.json",
    "token_file": "config/token.json",
    "scopes": ["https://www.googleapis.com/auth/spreadsheets"]
  },
  "nfc": {
    "timeout": 5,
    "retry_attempts": 3,
    "backend": "auto"
  },
  "stations": ["Reception", "Lio", "Juntos", "Experimental", "Unvrs"],
  "logging": {
    "level": "INFO",
    "file": "logs/TP_NFC.log",
    "max_size": "10MB",
    "backup_count": 5
  }
}
```