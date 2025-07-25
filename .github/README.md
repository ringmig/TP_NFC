# CI/CD Configuration

This directory contains GitHub Actions workflows for the TP_NFC project.

## Workflows

### 1. `ci-starter.yml` - Recommended Starting Point
**Use this workflow first!**

A simplified CI pipeline that focuses on essential checks:
- **Platforms**: Windows and macOS only (no Linux)
- **Python versions**: 3.9 and 3.10
- **Core checks**:
  - Flake8 linting (syntax errors fail the build)
  - pytest with coverage
  - Optional formatting checks (warnings only)

### 2. `ci.yml` - Comprehensive CI/CD Pipeline
**Switch to this after the starter works**

A complete CI/CD solution with:
- **Code quality**: black, isort, flake8, pylint, mypy
- **Security scanning**: bandit, safety, pip-audit
- **Multi-platform testing**: Windows, macOS
- **Build testing**: PyInstaller preparation for .exe/.app
- **Coverage reporting**: Codecov integration

### 3. `android-build.yml` - Android APK Build
Docker-based Android application build using Buildozer.

## Configuration Files

- **`.flake8`**: Flake8 linting configuration
- **`pyproject.toml`**: Tool configurations (black, isort, mypy, pytest, etc.)
- **`dependabot.yml`**: Automatic dependency updates

## Getting Started

1. **Start with the basic workflow**:
   ```bash
   # Rename the starter workflow to be active
   mv .github/workflows/ci.yml .github/workflows/ci-full.yml
   mv .github/workflows/ci-starter.yml .github/workflows/ci.yml
   ```

2. **Fix any immediate issues**:
   ```bash
   # Format your code to reduce warnings
   python format_code.py
   ```

3. **Commit and push** to trigger the CI

4. **Once stable, switch to full CI**:
   ```bash
   mv .github/workflows/ci.yml .github/workflows/ci-starter.yml
   mv .github/workflows/ci-full.yml .github/workflows/ci.yml
   ```

## Platform-Specific Notes

### Windows
- Uses Windows latest with Python 3.9/3.10
- PCSC (NFC) support should be built-in
- PyInstaller will create `.exe` files

### macOS
- Uses macOS latest with Python 3.10 (saves CI time)
- Installs `pcsc-lite` via Homebrew for NFC support
- py2app will create `.app` bundles

### Linux (Removed)
Since this is a desktop GUI application that will only be distributed for Windows and macOS, Linux testing has been removed to save CI resources.

## Future Enhancements

The workflows are designed to support:
- **Automated releases**: Tag-based releases with executable builds
- **Code signing**: For Windows .exe and macOS .app distribution
- **Notarization**: For macOS app store distribution
- **Multi-architecture**: ARM64 support for Apple Silicon

## Troubleshooting

### Common Issues

1. **Import errors**: Check that all dependencies are in `requirements.txt`
2. **NFC driver issues**: Platform-specific PCSC installation problems
3. **GUI testing**: CustomTkinter may need display server (use `pytest --no-gui`)
4. **Build failures**: PyInstaller may need additional `--hidden-import` flags

### Debugging CI

Check the logs in `.github/ci_logs/` (local development only - these are gitignored).

## Security

The CI includes security scanning with:
- **Bandit**: Python security linter
- **Safety**: Known vulnerability database
- **pip-audit**: Package vulnerability scanner

Review security reports and address any HIGH severity issues before release.