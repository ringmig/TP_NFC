# Configuration Options

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
    "window_mode": "maximized"
  }
}
```

### Other UI Options

- **`window_title`** - Text shown in the window title bar
- **`window_width`** - Window width in pixels (used in normal mode)
- **`window_height`** - Window height in pixels (used in normal mode)  
- **`theme`** - Color theme: `"dark-blue"`, `"green"`, `"blue"`

## Keyboard Shortcuts

- **F11** - Toggle between window modes
- **Cmd/Ctrl+R** - Refresh guest list
- **Cmd/Ctrl+F** - Focus search field
