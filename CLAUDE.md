# CLAUDE.md

## CRITICAL_BOOTSTRAP_PROTOCOL

LOAD_ORDER:
1. Read this file completely
2. Read `src/gui/app.py` to understand current implementation
3. Check `config/config.json` for runtime configuration

STATE_PERSISTENCE:
- Update this file after significant changes
- Include specific line numbers and method names
- Document in-progress operations and locks

## PROJECT_CONTEXT

PROJECT_NAME: TP_NFC
PROJECT_TYPE: NFC attendance tracking system
PRIMARY_LANGUAGE: Python 3.13.5
GUI_FRAMEWORK: CustomTkinter
PLATFORMS: Windows, macOS, Linux, Android

FILE_STRUCTURE:
```
C:\src\git\TP_NFC\
├── src/
│   ├── gui/app.py [MAIN_GUI: 4200+ lines]
│   ├── services/
│   │   ├── unified_nfc_service.py [NFC_BACKEND_ABSTRACTION]
│   │   ├── google_sheets_service.py [DATA_SYNC]
│   │   ├── tag_manager.py [TAG_GUEST_MAPPING]
│   │   └── check_in_queue.py [OFFLINE_QUEUE]
│   └── models/
├── python/ [WINDOWS_EMBEDDED_PYTHON_3.13.5]
├── config/
│   ├── config.json [RUNTIME_CONFIG]
│   ├── tag_registry.json [TAG_DATA]
│   └── check_in_queue.json [OFFLINE_DATA]
└── launchers/
    ├── start.bat [WINDOWS_LAUNCHER]
    └── start.command [MACOS_LAUNCHER]
```

## RECENT_MODIFICATIONS

LAST_SESSION_CHANGES:
1. TreeView width fix for registration mode (lines 4462-4520 in app.py)
   - ISSUE: Registration mode TreeView only used 45-60% of screen width, leaving empty space
   - METHOD: `_force_treeview_update()` at line 4462
   - SOLUTION: Removed explicit width constraints, used natural container expansion
   - COLUMN_CONFIG: Matched single station mode exactly (no stretch parameters)
   - RESULT: TreeView now uses full width with proper column proportions

2. Column configuration standardization (lines 4511-4514, 4471-4474)
   - REGISTRATION_MODE: id(80/60), first(150/100), last(150/100), wristband(200/150)
   - SINGLE_STATION: id(80/60), first(150/100), last(150/100), station(200/150)
   - CONSISTENCY: Both modes use identical sizing and anchor settings
   - NO_STRETCH: Removed explicit stretch parameters to match default behavior

3. Previous guest name display feature (lines 1785-1800, 2360-2403 in app.py)
   - METHOD: `_on_guest_id_change()` at line 2360
   - OPTIMIZATION: Changed from `sheets_service.find_guest_by_id()` to `self.guests_data` loop
   - PERFORMANCE: ~1000ms → ~5ms lookup time
   - UI_LOCATION: Above ID entry field, 36pt font
   - AUTO_CLEAR: Integrated with 15-second timer at line 4589

## CRITICAL_STATE_VARIABLES

GLOBAL_STATE_FLAGS:
- `self.operation_in_progress`: Mutex for preventing concurrent operations
- `self._nfc_operation_lock`: Prevents NFC scanning during write operations
- `self.is_registration_mode`: True at Reception station
- `self.is_checkpoint_mode`: True for check-in scanning
- `self.guests_data`: List[GuestRecord] - Cached guest data (397 entries typical)

THREAD_SAFETY_REQUIREMENTS:
- All UI updates from background threads MUST use `safe_update_widget()`
- Background operations use `submit_background_task()`
- NFC operations check `nfc_service.is_ready()` first

## KEY_METHOD_SIGNATURES

```python
# TreeView width forcing for registration mode (line 4462)
def _force_treeview_update(self):
    # Forces registration mode TreeView to use full width
    # Matches single station mode column configuration exactly
    # Called with 1ms delay after TreeView packing

# Guest name display optimization (line 2360)
def _on_guest_id_change(self, event=None):
    # Uses self.guests_data instead of API call
    # O(n) loop through ~397 guests

# Background task submission (line 492)
def submit_background_task(self, func, *args, **kwargs):
    # Returns Future object
    # Thread pool executor with 4 workers

# Safe UI updates from threads (line 508)
def safe_update_widget(self, widget_name, update_func, *args):
    # Thread-safe widget updates
    # Handles destroyed widgets gracefully
```

## OPERATIONAL_MODES

STATION_MODES:
1. Reception (default):
   - is_registration_mode = True
   - is_checkpoint_mode = True
   - Shows ID entry + guest name + register button
   
2. Other stations:
   - is_registration_mode = False
   - is_checkpoint_mode = True
   - Shows only scanning status

MODE_SWITCHING:
- Station buttons in header trigger `switch_station()`
- Updates both registration and checkpoint flags
- Calls `update_mode_content()` to rebuild UI

## PERFORMANCE_CRITICAL_PATHS

GUEST_LOOKUP_OPTIMIZATION:
- OLD: `self.sheets_service.find_guest_by_id(guest_id)` → API call → 500-2000ms
- NEW: Loop through `self.guests_data` → Memory lookup → 1-5ms
- DATA_SIZE: ~397 guests typical

UI_UPDATE_PATTERNS:
- TreeView updates use `_update_guest_table_silent()` for background refresh
- Status updates have type-based auto-clear timers
- NFC scanning has 5-second retry on "no tag detected"

## CONFIGURATION_DEPENDENCIES

EMBEDDED_PYTHON_WINDOWS:
- Location: `python/python.exe`
- Packages: `python/Lib/site-packages/`
- Path config: `python313._pth`

RUNTIME_CONFIGURATION:
- Dark mode: `config.json` → `appearance_mode`
- Window mode: `config.json` → `window_mode` (maximized/fullscreen)
- Stations: `config.json` → `stations` list
- Developer password: `config.json` → `developer.password` (default: 8888)

## ERROR_HANDLING_PATTERNS

NFC_ERRORS:
- No reader: Shows persistent error in status bar
- Tag read failure: 5-second retry with countdown
- Duplicate scan: 3-second cooldown

NETWORK_ERRORS:
- Offline mode: Queue check-ins locally
- Sync retry: Background thread every 30 seconds
- Internet check: Lightweight ping every 10 seconds

## CURRENT_ISSUES

KNOWN_BUGS:
- None critical

OPTIMIZATION_OPPORTUNITIES:
- TreeView could use virtual rendering for large guest lists
- Check-in queue could batch API calls
- Status messages could use priority queue

## BUILD_COMMANDS

WINDOWS_RUN:
```
cd C:\src\git\TP_NFC
python\python.exe src\main.py
```

LAUNCHER_RUN:
```
C:\src\git\TP_NFC\launchers\start.bat
```

TEST_COMMANDS:
```
python\python.exe -m pytest
python\Scripts\flake8.exe src
```