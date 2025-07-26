# Contributing to TP_NFC

Thank you for your interest in contributing to TP_NFC! This guide will help you get started with contributing to the project.

## Getting Started

### Development Setup

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/TP_NFC.git
   cd TP_NFC
   ```
3. **Set up development environment**:
   ```bash
   ./install.command  # macOS/Linux
   # or install.bat   # Windows
   ```
4. **Install development dependencies**:
   ```bash
   pip install flake8 mypy pytest pytest-cov black isort bandit safety
   ```

### Before You Start

- **Check existing issues** - someone might already be working on it
- **Create an issue** to discuss major changes before implementing
- **Read the documentation** in `docs/` to understand the architecture
- **Test your hardware setup** with the diagnostic tools

## How to Contribute

### Types of Contributions

**Bug Reports**
- Use the issue template
- Include system information (OS, Python version, hardware)
- Provide steps to reproduce
- Include relevant log files

**Feature Requests**
- Describe the use case and problem being solved
- Consider backward compatibility
- Provide mockups or examples if applicable

**Code Contributions**
- Bug fixes
- New features
- Performance improvements
- Documentation improvements
- Test coverage improvements

### Development Workflow

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   # or fix/your-bug-description
   ```

2. **Make your changes** following the coding standards below

3. **Test your changes**:
   ```bash
   # Run tests
   pytest
   
   # Test manually
   python src/main.py
   
   # Test with hardware
   tools/test_nfc.command
   tools/test_sheets.command
   ```

4. **Commit with clear messages**:
   ```bash
   git commit -m "feat(nfc): add support for NTAG216 tags"
   ```

5. **Push and create pull request**:
   ```bash
   git push origin feature/your-feature-name
   ```

## Coding Standards

### Code Style

**Follow PEP 8**:
```bash
# Format code before committing
black src/
isort src/

# Check for issues
flake8 src/
mypy src/
```

**Naming Conventions**:
- Classes: `PascalCase` (e.g., `NFCService`)
- Functions/variables: `snake_case` (e.g., `read_tag`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`)
- Private methods: `_leading_underscore`

### Documentation

**Docstrings for public methods**:
```python
def read_tag(self, timeout: int = 5) -> Optional[NFCTag]:
    """
    Read an NFC tag from the reader.
    
    Args:
        timeout: Maximum time to wait for tag in seconds
        
    Returns:
        NFCTag object if successful, None if no tag detected
        
    Raises:
        NFCError: If reader hardware error occurs
    """
```

**Comments for complex logic**:
```python
# Use exponential backoff for retries to avoid overwhelming the API
wait_time = 2 ** attempt
```

### Error Handling

**Comprehensive exception handling**:
```python
try:
    result = risky_operation()
except SpecificError as e:
    self.logger.error(f"Specific error occurred: {e}")
    # Handle gracefully
except Exception as e:
    self.logger.error(f"Unexpected error: {e}")
    raise  # Re-raise if can't handle
```

**User-friendly error messages**:
```python
# Bad
raise Exception("Error 123")

# Good  
raise NFCError("NFC reader not found. Please check USB connection and drivers.")
```

### Threading

**UI updates only on main thread**:
```python
# From background thread
def background_operation(self):
    result = long_running_task()
    # Schedule UI update on main thread
    self.after(0, self.update_ui, result)
```

**Proper cleanup**:
```python
def start_operation(self):
    self.operation_in_progress = True
    try:
        # Perform operation
        pass
    finally:
        self.operation_in_progress = False
```

## Testing Guidelines

### Test Requirements

**New features must include tests**:
- Unit tests for business logic
- Integration tests for service interactions
- Manual testing procedures for hardware

**Test Structure**:
```python
import pytest
from unittest.mock import Mock, patch
from src.services.nfc_service import NFCService

class TestNFCService:
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.nfc_service = NFCService()
    
    def test_successful_tag_read(self):
        """Test successful tag reading scenario."""
        with patch('nfcpy.ContactlessFrontend') as mock_clf:
            mock_clf.return_value.connect.return_value = True
            result = self.nfc_service.read_tag()
            assert result is not None
    
    def test_hardware_error_handling(self):
        """Test proper error handling when hardware fails."""
        with patch('nfcpy.ContactlessFrontend') as mock_clf:
            mock_clf.side_effect = Exception("Hardware error")
            result = self.nfc_service.read_tag()
            assert result is None
```

### Manual Testing

**Before submitting pull request**:
- [ ] Application starts without errors
- [ ] Core functionality works (registration, check-in)
- [ ] Error scenarios handled gracefully
- [ ] UI remains responsive during operations
- [ ] No memory leaks during extended use

**Hardware Testing (if applicable)**:
- [ ] Test with real NFC reader
- [ ] Test with different tag types
- [ ] Test disconnection/reconnection scenarios

## Pull Request Guidelines

### Pull Request Checklist

- [ ] **Code follows style guidelines** (black, flake8, mypy)
- [ ] **Tests pass** (`pytest`)
- [ ] **New functionality includes tests**
- [ ] **Documentation updated** (if user-facing changes)
- [ ] **No security vulnerabilities** (`bandit -r src/`)
- [ ] **Performance impact considered**
- [ ] **Backward compatibility maintained**

### Pull Request Description

**Include in your PR description**:
- **What**: Brief description of changes
- **Why**: Problem being solved or feature being added
- **How**: Approach taken and key implementation details
- **Testing**: How the changes were tested
- **Screenshots**: For UI changes

**Example**:
```markdown
## What
Add support for NTAG216 tags in addition to NTAG213

## Why
Users have requested support for higher capacity tags for storing additional metadata

## How
- Extended tag detection logic in NFCService
- Added NTAG216 constants and memory layout
- Updated tag writing methods to handle different capacities

## Testing
- Unit tests for new tag type detection
- Manual testing with physical NTAG216 tags
- Verified backward compatibility with NTAG213

## Breaking Changes
None - fully backward compatible
```

### Commit Message Format

```
type(scope): brief description

Optional longer description explaining the change in more detail.

Fixes #123
Closes #456
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only changes
- `style`: Code style changes (formatting, missing semicolons, etc)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Performance improvements
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to build process, auxiliary tools, libraries

## Review Process

### What Reviewers Look For

**Code Quality**:
- Follows established patterns in the codebase
- Proper error handling and edge cases
- Performance implications considered
- Security best practices followed

**Architecture**:
- Changes fit within existing architecture
- Proper separation of concerns maintained
- Thread safety preserved
- State management handled correctly

**User Experience**:
- UI changes are intuitive and consistent
- Error messages are helpful
- Operations provide appropriate feedback
- Accessibility considerations

### Addressing Review Feedback

- **Respond promptly** to review comments
- **Ask for clarification** if feedback is unclear
- **Make requested changes** in new commits (don't force push)
- **Update tests** if implementation changes
- **Re-request review** when ready

## Community Guidelines

### Communication

- **Be respectful** and constructive in all interactions
- **Ask questions** if something is unclear
- **Help others** when you can
- **Share knowledge** and lessons learned

### Getting Help

**If you're stuck**:
1. Check the documentation in `docs/`
2. Search existing issues and discussions
3. Create an issue with your question
4. Join discussions in existing issues

**For urgent issues**:
- Check if it's a security issue (report privately)
- Look for workarounds in troubleshooting guide
- Create issue with "urgent" label if affecting production use

## Release Process

### Feature Freeze

- **2 weeks before release**: Feature freeze begins
- **1 week before release**: Bug fixes and testing only
- **Release day**: Final testing and release preparation

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):
- **Major**: Breaking changes to API or configuration
- **Minor**: New features, backward compatible
- **Patch**: Bug fixes, security updates

## Recognition

Contributors will be:
- **Listed in CONTRIBUTORS.md**
- **Mentioned in release notes** for significant contributions
- **Invited to join** maintainer discussions for ongoing contributors

Thank you for contributing to TP_NFC! 🎉