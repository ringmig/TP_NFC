# Development Guide

## Getting Started

### Development Environment Setup

**Clone and Setup:**
```bash
git clone https://github.com/ringmig/TP_NFC.git
cd TP_NFC
./install.command  # macOS/Linux
# or install.bat  # Windows
```

**Development Dependencies:**
```bash
# Install additional dev tools
pip install flake8 mypy pytest pytest-cov black isort bandit safety
```

**IDE Setup:**
- **VS Code**: Recommended with Python extension
- **PyCharm**: Full IDE support
- **Vim/Emacs**: Works with language servers

### Running in Development Mode

```bash
# Direct execution
python src/main.py

# With debug logging
LOGLEVEL=DEBUG python src/main.py

# Development server (if applicable)
python -m src.main --dev
```

## Code Organization

### Architecture Principles

**Separation of Concerns:**
- **GUI Layer** (`src/gui/`): UI components and user interactions
- **Service Layer** (`src/services/`): Business logic and external integrations  
- **Data Layer** (`src/models/`): Data structures and persistence
- **Utilities** (`src/utils/`): Shared functionality and helpers

**Dependency Flow:**
```
GUI → Services → Models
    ↘ Utils ↙
```

### Key Design Patterns

**State Management:**
- Central state in main GUI class
- Operation flags prevent race conditions
- Clean state transitions with proper cleanup

**Thread Safety:**
- UI updates only on main thread via `self.after()`
- Background operations in ThreadPoolExecutor
- Proper synchronization with locks and flags

**Error Handling:**
- Comprehensive exception handling at service boundaries
- User-friendly error messages with recovery suggestions
- Graceful degradation when services unavailable

## Development Guidelines

### Code Style

**Follow PEP 8:**
```bash
# Format code
black src/
isort src/

# Lint
flake8 src/

# Type checking
mypy src/
```

**Naming Conventions:**
- **Classes**: `PascalCase` (e.g., `NFCService`)
- **Functions/Variables**: `snake_case` (e.g., `get_guest_data`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRY_ATTEMPTS`)
- **Private Methods**: `_leading_underscore` (e.g., `_internal_method`)

**Documentation:**
```python
def complex_function(param1: str, param2: int = 5) -> Optional[Dict[str, Any]]:
    """
    Brief description of what the function does.
    
    Args:
        param1: Description of first parameter
        param2: Description of second parameter (default: 5)
        
    Returns:
        Description of return value, or None if error
        
    Raises:
        ValueError: When param1 is invalid
        ConnectionError: When service unavailable
    """
```

### State Management Patterns

**Operation Flags:**
```python
# Prevent concurrent operations
if self.operation_in_progress:
    return
    
self.operation_in_progress = True
try:
    # Perform operation
    pass
finally:
    self.operation_in_progress = False
```

**Thread-Safe UI Updates:**
```python
# From background thread
def _background_operation(self):
    try:
        result = some_long_operation()
        # Schedule UI update on main thread
        self.after(0, self._update_ui_with_result, result)
    except Exception as e:
        self.after(0, self._handle_error, str(e))
```

**Mode Transitions:**
```python
def enter_rewrite_mode(self):
    # Save current state
    self._previous_mode = self.current_mode
    self._previous_scanning = self.is_scanning
    
    # Stop current operations
    self.stop_scanning()
    
    # Enter new mode
    self.is_rewrite_mode = True
    self.update_mode_content()

def exit_rewrite_mode(self):
    # Restore previous state
    self.is_rewrite_mode = False
    self.current_mode = self._previous_mode
    
    # Resume operations if needed
    if self._previous_scanning:
        self.start_scanning()
```

## Testing

### Manual Testing

**Hardware Tests:**
```bash
# Test NFC reader
tools/test_nfc.command

# Test Google Sheets
tools/test_sheets.command

# Comprehensive diagnostics
tools/diagnose_nfc.command
```

**Integration Tests:**
```bash
# Full application test
python src/main.py

# Specific component tests
python -m src.services.unified_nfc_service --test
python -m src.services.google_sheets_service --test
```

### Unit Testing

**Run Tests:**
```bash
# All tests
pytest

# With coverage
pytest --cov=src

# Specific test file
pytest tests/test_nfc_service.py

# Verbose output
pytest -v
```

**Writing Tests:**
```python
import pytest
from unittest.mock import Mock, patch
from src.services.nfc_service import NFCService

class TestNFCService:
    def setup_method(self):
        self.nfc_service = NFCService()
    
    def test_tag_detection(self):
        # Test tag detection logic
        with patch('src.services.nfc_service.nfc.ContactlessFrontend') as mock_clf:
            mock_clf.return_value.connect.return_value = True
            result = self.nfc_service.read_tag()
            assert result is not None
    
    def test_error_handling(self):
        # Test error scenarios
        with patch('src.services.nfc_service.nfc.ContactlessFrontend') as mock_clf:
            mock_clf.side_effect = Exception("Hardware error")
            result = self.nfc_service.read_tag()
            assert result is None
```

### Security Testing

**Security Scanning:**
```bash
# Check for security issues
bandit -r src/

# Check dependencies
safety check

# Check for secrets
git-secrets --scan
```

## Key Components Deep Dive

### GUI Development (`src/gui/app.py`)

**Widget Management:**
```python
# Safe widget updates from background threads
def safe_update_widget(self, widget_name, update_func):
    """Safely update widget from any thread."""
    def _update():
        if hasattr(self, widget_name):
            widget = getattr(self, widget_name)
            if widget.winfo_exists():
                update_func(widget)
    
    self.after(0, _update)

# Usage
self.safe_update_widget('status_label', 
                       lambda w: w.configure(text="Updated"))
```

**Event Binding:**
```python
# Proper event binding with cleanup
def setup_bindings(self):
    self.bind('<KeyPress>', self.on_key_press)
    self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
def cleanup_bindings(self):
    self.unbind('<KeyPress>')
```

### Service Development

**Service Base Pattern:**
```python
class BaseService:
    def __init__(self, config: dict, logger):
        self.config = config
        self.logger = logger
        self._connected = False
    
    def connect(self) -> bool:
        """Establish connection to service."""
        try:
            # Connection logic
            self._connected = True
            return True
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return False
    
    def is_ready(self) -> bool:
        """Check if service is ready for operations."""
        return self._connected
    
    def disconnect(self):
        """Clean disconnect from service."""
        self._connected = False
```

**Error Handling Pattern:**
```python
def robust_operation(self, *args, **kwargs):
    """Template for robust service operations."""
    if not self.is_ready():
        raise ServiceNotReadyError("Service not connected")
    
    for attempt in range(self.max_retries):
        try:
            return self._perform_operation(*args, **kwargs)
        except RetryableError as e:
            if attempt < self.max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                time.sleep(wait_time)
                continue
            raise
        except NonRetryableError:
            raise
    
    raise MaxRetriesExceededError()
```

## Common Development Tasks

### Adding New Features

**1. New NFC Operation:**
```python
# 1. Add to NFCService
def new_nfc_operation(self, tag_data):
    """Implement new NFC functionality."""
    pass

# 2. Add to TagManager coordination
def coordinate_new_operation(self, guest_id):
    """Coordinate with other services."""
    pass

# 3. Add UI integration in app.py
def handle_new_operation(self):
    """Handle UI for new operation."""
    pass
```

**2. New Configuration Option:**
```python
# 1. Add to config.json schema
{
  "new_feature": {
    "enabled": true,
    "timeout": 30
  }
}

# 2. Add validation
def validate_config(config):
    new_feature = config.get('new_feature', {})
    if not isinstance(new_feature.get('timeout'), int):
        raise ConfigError("new_feature.timeout must be integer")

# 3. Use in service
class SomeService:
    def __init__(self, config):
        self.feature_enabled = config.get('new_feature', {}).get('enabled', False)
        self.timeout = config.get('new_feature', {}).get('timeout', 30)
```

### Debugging Common Issues

**Threading Issues:**
```python
# Add debug logging
import threading
self.logger.debug(f"Current thread: {threading.current_thread().name}")

# Check for UI updates from wrong thread
if threading.current_thread() != threading.main_thread():
    self.logger.warning("UI update from background thread!")
```

**State Management:**
```python
# Log state transitions
def set_operation_in_progress(self, value, reason=""):
    old_value = self.operation_in_progress
    self.operation_in_progress = value
    self.logger.debug(f"Operation flag: {old_value} -> {value} ({reason})")
```

**Performance Issues:**
```python
import time

# Time critical operations
start_time = time.time()
result = expensive_operation()
duration = time.time() - start_time
self.logger.info(f"Operation took {duration:.2f} seconds")

# Profile memory usage
import psutil
process = psutil.Process()
memory_mb = process.memory_info().rss / 1024 / 1024
self.logger.debug(f"Memory usage: {memory_mb:.1f} MB")
```

## Release Process

### Pre-release Checklist

**Code Quality:**
- [ ] All tests passing (`pytest`)
- [ ] Code formatted (`black src/`)
- [ ] Imports sorted (`isort src/`)
- [ ] No linting errors (`flake8 src/`)
- [ ] Type checking clean (`mypy src/`)
- [ ] Security scan clean (`bandit -r src/`)

**Functionality:**
- [ ] Manual testing on target platforms
- [ ] Hardware testing with real NFC readers
- [ ] Google Sheets integration verified
- [ ] Performance testing with large datasets
- [ ] Error handling tested

**Documentation:**
- [ ] README updated
- [ ] CHANGELOG updated
- [ ] API documentation current
- [ ] Configuration examples valid

### Version Management

**Semantic Versioning:**
- **Major**: Breaking changes to API or configuration
- **Minor**: New features, backward compatible
- **Patch**: Bug fixes, no new features

**Release Tags:**
```bash
# Create release
git tag -a v1.2.3 -m "Release version 1.2.3"
git push origin v1.2.3

# Update version in code
echo "VERSION = '1.2.3'" > src/version.py
```

## Contributing Guidelines

### Pull Request Process

1. **Fork** the repository
2. **Create feature branch** from `main`
3. **Implement changes** following coding standards
4. **Add tests** for new functionality
5. **Update documentation** as needed
6. **Test thoroughly** on target platforms
7. **Submit pull request** with clear description

### Code Review Standards

**Review Checklist:**
- [ ] Code follows style guidelines
- [ ] Tests cover new functionality
- [ ] Documentation updated
- [ ] No security vulnerabilities
- [ ] Performance impact considered
- [ ] Error handling appropriate
- [ ] Thread safety maintained

### Commit Guidelines

**Commit Message Format:**
```
type(scope): description

Optional longer description

Fixes #123
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix  
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Build/tooling changes

## Resources

### Development Tools

**Recommended Extensions (VS Code):**
- Python
- Python Docstring Generator
- GitLens
- Python Type Hint
- autoDocstring

**Useful Libraries:**
- `pytest` - Testing framework
- `black` - Code formatting
- `isort` - Import sorting
- `mypy` - Type checking
- `flake8` - Linting

### Learning Resources

**Python GUI Development:**
- [CustomTkinter Documentation](https://customtkinter.tomschimansky.com/)
- [Tkinter Threading Best Practices](https://tkdocs.com/tutorial/index.html)

**NFC Development:**
- [nfcpy Documentation](https://nfcpy.readthedocs.io/)
- [PC/SC Workgroup](https://pcscworkgroup.com/)

**Google Sheets API:**
- [Google Sheets API Documentation](https://developers.google.com/sheets/api)
- [OAuth2 for Desktop Apps](https://developers.google.com/identity/protocols/oauth2/native-app)