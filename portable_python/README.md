# Portable Python Distribution

This directory contains embeddable Python distributions for different platforms.

## Directory Structure
```
portable_python/
├── windows/           # Windows embeddable Python
│   ├── python.exe
│   ├── python311.zip
│   └── ...
├── macos/             # macOS standalone Python
│   ├── bin/
│   ├── lib/
│   └── ...
└── README.md
```

## Download Instructions

### Windows (Embeddable Python)
1. Go to https://www.python.org/downloads/windows/
2. Download "Windows embeddable package (64-bit)" for Python 3.11+
3. Extract contents to `portable_python/windows/`

### macOS (Automatic Setup)
**No manual download needed!** The `install_portable.command` script will:
1. Install the `portable-python` package automatically
2. Download and set up Python 3.11 in `portable_python/macos/`
3. Configure everything for you

### macOS (Manual Setup - if needed)
1. Go to https://www.python.org/downloads/macos/
2. Download the macOS installer for Python 3.11+
3. Install normally, then copy the Python.framework to `portable_python/macos/`

Alternative: Use pyenv to create a relocatable Python installation.

## Setup Process
After downloading Python:
1. Run the updated install scripts
2. Dependencies will be installed to `portable_python/site-packages/`
3. The application will run completely standalone