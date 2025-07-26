# Architecture Overview

## System Design

TP_NFC is designed as a modular, cross-platform desktop application with clear separation of concerns and robust error handling.

### Core Principles

**Offline-First Design**
- Local queue system for reliability during network outages
- Cached guest data for offline operation
- Background sync when connectivity restored

**Thread Safety**
- UI updates via main thread scheduling (`self.after()`)
- Background operations in ThreadPoolExecutor
- Proper widget lifecycle management

**Cross-Platform Compatibility**
- Automatic NFC backend selection (nfcpy vs pyscard)
- Platform-specific optimizations
- Unified configuration system

## Project Structure

```
TP_NFC/
├── src/                             # Source code
│   ├── main.py                     # Application entry point
│   ├── gui/
│   │   └── app.py                  # Main GUI (4000+ lines)
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
├── config/                         # Configuration and data
├── docs/                          # Documentation
├── tools/                         # Testing utilities
└── logs/                          # Application logs
```

## Key Components

### GUI Layer (`src/gui/app.py`)

**Responsibilities:**
- User interface management and state coordination
- Event handling and user interaction
- Thread-safe UI updates from background operations
- Mode management (Registration, Checkpoint, Settings, Rewrite)

**Design Patterns:**
- **State Machine**: Clear mode transitions with proper cleanup
- **Observer Pattern**: Status updates and sync completion callbacks
- **Command Pattern**: Background task submission and result handling

**Key Features:**
- Modern CustomTkinter interface with theme support
- Complex state management with operation locks
- Background scanning with cancellation support
- Real-time search and filtering

### Service Layer

#### NFC Service (`unified_nfc_service.py`)
- **Auto-detection**: Automatically selects best NFC backend for platform
- **Error Recovery**: Robust handling of hardware disconnections
- **Thread Safety**: Proper cleanup and cancellation patterns
- **Performance**: Optimized timing loops (3-5 second cycles)

#### Google Sheets Service (`google_sheets_service.py`)
- **OAuth2 Management**: Token handling and refresh
- **Dynamic Detection**: Auto-discovers station columns from headers
- **Batch Operations**: Efficient bulk updates with rate limiting
- **Caching**: Guest data persistence for offline operation
- **Retry Logic**: Exponential backoff for network failures

#### Tag Manager (`tag_manager.py`)
- **Coordination**: Links NFC operations with Google Sheets updates
- **Registry Management**: Persistent tag-to-guest mappings with backup
- **Conflict Resolution**: Handles duplicate registrations and sync conflicts
- **Queue Integration**: Manages check-in queue for offline reliability

#### Check-in Queue (`check_in_queue.py`)
- **Offline Queue**: Local persistence during network outages
- **Background Sync**: Automatic sync when connectivity restored
- **Conflict Resolution**: Handles data discrepancies between local and remote
- **Atomic Operations**: Ensures data consistency during failures

### Data Models

#### GuestRecord (`guest_record.py`)
- **Dynamic Stations**: Supports variable station configurations
- **Check-in Tracking**: Timestamps and status for each station
- **Mobile Integration**: Phone number support for tooltips
- **Serialization**: JSON persistence for caching

#### NFCTag (`nfc_tag.py`)
- **Hardware Abstraction**: Unified interface for different tag types
- **Guest Association**: Links tags to guest records
- **Metadata**: Creation timestamps and registration history

## Threading Architecture

### Main Thread
- **UI Updates**: All widget modifications
- **Event Handling**: User interactions and callbacks
- **State Management**: Mode transitions and operation coordination

### Background Threads
- **NFC Operations**: Tag reading/writing with timeout handling
- **Google Sheets API**: Network requests with retry logic
- **File I/O**: Configuration and log file operations
- **Periodic Tasks**: Internet monitoring and auto-refresh

### Synchronization Patterns

**Operation Locks:**
```python
self.operation_in_progress = False     # Prevents concurrent user operations
self._active_operations = 0            # Counts background tasks
self._nfc_operation_lock = False       # Prevents NFC conflicts
```

**Thread-Safe UI Updates:**
```python
# From background thread
self.after(0, self.update_status, message, status_type)

# Safe widget access
def _safe_configure_widget(self, widget_name, **kwargs):
    if hasattr(self, widget_name):
        widget = getattr(self, widget_name)
        if widget.winfo_exists():
            widget.configure(**kwargs)
```

## State Management

### Application Modes

**Reception Station:**
- Registration Mode: Tag writing with auto-check-in
- Checkpoint Mode: Continuous scanning for check-ins

**Other Stations:**
- Checkpoint-only: No registration functionality
- Multi-station support with dynamic detection

**Overlay Modes:**
- Settings Panel: Non-blocking overlay with state restoration
- Rewrite Mode: Isolated mode with forced return path
- Tag Info Display: Temporary display with auto-close

### State Restoration

**Settings Panel:**
- Remembers previous station and mode
- Resumes background scanning if appropriate
- Maintains operation flags during transition

**Tag Info Display:**
- Returns to exact triggering state
- Handles both settings and station origins
- Preserves scanning state across display

**Error Recovery:**
- Automatic cleanup of stuck operations
- State reset on unrecoverable errors
- Graceful degradation patterns

## Data Flow

### Tag Registration Flow
1. User enters guest ID → Validate against Google Sheets
2. NFC tag detected → Check for existing registration
3. Tag written → Update local registry + Google Sheets
4. Auto check-in → Add to queue → Background sync

### Check-in Flow  
1. NFC tag detected → Look up in local registry
2. Guest identified → Check for duplicates
3. Add to local queue → Immediate UI feedback
4. Background sync → Update Google Sheets
5. Sync completion → UI status update

### Offline Operation
1. Network loss detected → Switch to offline mode
2. Queue all operations locally → Show offline indicators
3. Periodic connectivity check → Detect restoration
4. Automatic sync → Resolve conflicts → Update UI

## Security Considerations

**Data Protection:**
- Google credentials stored locally only
- NFC tags contain only guest IDs (no personal data)
- Local files protected by filesystem permissions
- OAuth tokens with appropriate scopes

**Network Security:**
- HTTPS for all Google API communications
- OAuth2 with refresh tokens
- No sensitive data in logs
- Secure token storage and rotation

**Physical Security:**
- NFC read range limited to 1-4cm
- Tag UIDs are not predictable
- Guest IDs require spreadsheet access to be meaningful
- Local registry backup and recovery

## Performance Optimizations

**NFC Operations:**
- Short timeout loops (3-5 seconds) for responsiveness
- Background scanning with proper cancellation
- Hardware connection pooling and cleanup

**Google Sheets:**
- Batch operations for efficiency
- Intelligent caching with TTL
- Rate limiting compliance
- Background sync to avoid UI blocking

**UI Performance:**
- Lazy loading of guest data
- Virtual scrolling for large datasets
- Debounced search filtering
- Efficient theme switching

**Memory Management:**
- Proper widget cleanup and reference clearing
- Log rotation to prevent disk usage growth
- Cache eviction policies
- Background task lifecycle management

## Error Handling Strategy

**Graceful Degradation:**
- Offline mode when network unavailable
- Cached data when API fails
- Manual operations when NFC unavailable
- Fallback UI states for all scenarios

**User-Friendly Errors:**
- Clear error messages with suggested actions
- Status indicators for system health
- Automatic retry with exponential backoff
- Diagnostic tools for troubleshooting

**Recovery Mechanisms:**
- Automatic state cleanup after timeouts
- Operation cancellation and restart
- Data consistency checks and repair
- Backup and restore capabilities

## Extensibility

**Plugin Architecture:**
- Service layer abstraction for easy extension
- Configuration-driven station management
- Modular NFC backend system
- Event system for custom integrations

**Configuration System:**
- JSON-based configuration with validation
- Runtime configuration updates
- Environment-specific overrides
- Backward compatibility maintenance

**API Design:**
- Clear separation between layers
- Consistent error handling patterns
- Documented interfaces for services
- Future-proof data models