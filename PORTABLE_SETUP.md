# TP_NFC Portable Distribution Setup

This guide explains how to create a completely portable, standalone version of TP_NFC that can be copied to any computer without requiring Python installation.

## Quick Start

### For End Users (Receiving a Portable Distribution)
1. Copy the entire TP_NFC folder to your computer
2. Go to the `launchers/` folder and choose your preferred launcher:
   - **Recommended**: `start_hidden.command` (macOS) - Cleanest experience
   - **Alternative**: `start.command` (macOS) - Traditional launcher  
   - **Windows**: `start.bat` - For Windows machines
3. Create a shortcut to your chosen launcher for easy access
4. The application will launch without any setup required!

### For Developers (Creating a Portable Distribution)
Follow the detailed setup below.

## Detailed Setup Instructions

### Step 1: Download Portable Python

#### Windows
1. Go to https://www.python.org/downloads/windows/
2. Find Python 3.11 or later
3. Download **"Windows embeddable package (64-bit)"**
4. Extract the contents to `portable_python/windows/`

Your structure should look like:
```
TP_NFC/
├── portable_python/
│   └── windows/
│       ├── python.exe
│       ├── python311.zip
│       ├── python311._pth
│       └── ... (other files)
```

#### macOS (Automatic)
**The install script will handle this automatically!** Just run:
```bash
./install.command
```

The script will:
1. Install the `portable-python` package
2. Download and set up Python 3.11 automatically
3. Create the portable distribution

#### macOS (Manual - if automatic fails)
1. Go to https://www.python.org/downloads/macos/
2. Download Python 3.11+ installer
3. Install Python normally
4. Copy the Python framework:
   ```bash
   cp -r /Library/Frameworks/Python.framework/Versions/3.11 portable_python/macos/
   ```

Alternative (using Homebrew):
```bash
# Install pyenv for portable Python builds
brew install pyenv
pyenv install 3.11.8
cp -r ~/.pyenv/versions/3.11.8 portable_python/macos/
```

### Step 2: Install Dependencies
Run the portable installation script:

**Windows:**
```cmd
install.bat
```

**macOS:**
```bash
./install.command
```

### Step 3: Test the Installation
Launch the portable application:

**Windows:**
```cmd
start.bat
```

**macOS:**
```bash
./start.command
```

## Distribution Structure

After setup, your portable distribution will contain:

```
TP_NFC/
├── portable_python/
│   ├── windows/           # Windows embeddable Python
│   ├── macos/             # macOS portable Python  
│   └── site-packages/     # All Python dependencies
├── src/                   # Application source code
├── config/                # Configuration files
├── logs/                  # Application logs
├── start.bat              # Windows launcher
├── start.command          # macOS launcher
├── install.bat            # Windows installer
├── install.command        # macOS installer
├── start_legacy.bat       # Legacy venv launcher (Windows)
├── start_legacy.command   # Legacy venv launcher (macOS)
├── install_legacy.bat     # Legacy venv installer (Windows)
├── install_legacy.command # Legacy venv installer (macOS)
└── requirements.txt       # Dependencies list
```

## How It Works

### Traditional Installation (requires Python)
```
User's Computer → System Python → pip install → venv → Run App
```

### Portable Installation (no Python required)
```
Portable Folder → Bundled Python → Bundled Packages → Run App
```

## Advantages

✅ **No Python installation required** on target machines  
✅ **No pip or package management** needed  
✅ **Version consistency** - same Python version everywhere  
✅ **Dependency isolation** - no conflicts with system packages  
✅ **Easy distribution** - just copy the folder  
✅ **Works offline** - no internet required for dependencies  
✅ **Cross-platform** - same approach for Windows and macOS  

## File Sizes

- **Windows**: ~50-70 MB (Python + dependencies)
- **macOS**: ~80-100 MB (Python + dependencies)
- **Source Code**: ~5 MB

## Security Considerations

- Python and all dependencies are bundled and known versions
- No external package downloads during runtime
- All code is visible and auditable
- No system modifications required

## Troubleshooting

### "Python not found" error
- Ensure portable Python is extracted to the correct directory
- Check that `python.exe` (Windows) or `bin/python3` (macOS) exists

### "Module not found" error
- Re-run the portable installation script
- Check that `portable_python/site-packages/` contains the dependencies

### Application won't start
- Try running from terminal/command prompt to see error messages
- Ensure all files were copied (check file permissions on macOS)

## Distribution Checklist

Before distributing to other computers:

- [ ] Portable Python is installed in correct directory
- [ ] Dependencies are installed to site-packages
- [ ] Application launches successfully with portable scripts
- [ ] Configuration files are set up (Google Sheets ID, etc.)
- [ ] Test on a clean machine without Python installed

## Updates

To update a portable distribution:
1. Copy new source code to `src/` directory
2. Run portable install script if new dependencies were added
3. Update configuration files if needed

The portable Python and packages don't need to be updated unless there are security patches or new dependency requirements.