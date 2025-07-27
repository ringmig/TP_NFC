@echo off
REM TP_NFC Portable Installation Script for Windows

echo TP_NFC Portable Installation
echo ============================
echo.

REM Get script directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Check if portable Python exists
set "PORTABLE_PYTHON_DIR=%SCRIPT_DIR%portable_python\windows"
set "PYTHON_EXECUTABLE="

if exist "%PORTABLE_PYTHON_DIR%\python.exe" (
    echo Using portable Python distribution...
    set "PYTHON_EXECUTABLE=%PORTABLE_PYTHON_DIR%\python.exe"
    echo Portable Python version:
    "%PYTHON_EXECUTABLE%" --version
) else (
    REM Check for system Python
    python --version >nul 2>&1
    if %errorlevel% equ 0 (
        echo Portable Python not found, using system Python...
        set "PYTHON_EXECUTABLE=python"
        echo System Python version:
        python --version
    ) else (
        echo Error: No Python 3 installation found.
        echo.
        echo For portable mode:
        echo 1. Download "Windows embeddable package (64-bit)" from https://www.python.org/downloads/windows/
        echo 2. Extract to portable_python\windows\ directory
        echo.
        echo Or install system Python from https://www.python.org/downloads/
        echo.
        pause
        exit /b 1
    )
)

echo.

REM Set up portable site-packages directory
set "SITE_PACKAGES_DIR=%SCRIPT_DIR%portable_python\site-packages"
echo Setting up portable site-packages directory...
if not exist "%SITE_PACKAGES_DIR%" mkdir "%SITE_PACKAGES_DIR%"

REM Remove existing virtual environment if it exists
if exist "venv" (
    echo Removing existing virtual environment...
    rmdir /s /q "venv"
)

REM For Windows embeddable Python, we need to modify python313._pth
if exist "%PORTABLE_PYTHON_DIR%\python313._pth" (
    echo Configuring portable Python path...
    echo import site >> "%PORTABLE_PYTHON_DIR%\python313._pth"
    echo ../site-packages >> "%PORTABLE_PYTHON_DIR%\python313._pth"
)

REM Install get-pip if needed for embeddable Python
if exist "%PORTABLE_PYTHON_DIR%\python.exe" (
    if not exist "%PORTABLE_PYTHON_DIR%\Scripts\pip.exe" (
        echo Installing pip for portable Python...
        powershell -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'get-pip.py'"
        "%PYTHON_EXECUTABLE%" get-pip.py --target "%SITE_PACKAGES_DIR%"
        del get-pip.py
    )
)

REM Install dependencies
echo Installing dependencies to portable directory...
"%PYTHON_EXECUTABLE%" -m pip install --target "%SITE_PACKAGES_DIR%" --upgrade pip
"%PYTHON_EXECUTABLE%" -m pip install --target "%SITE_PACKAGES_DIR%" -r requirements.txt

REM Create necessary directories
echo.
echo Creating necessary directories...
if not exist "logs" mkdir "logs"
if not exist "config" mkdir "config"

REM Create tag registry file if it doesn't exist
if not exist "config\tag_registry.json" (
    echo {} > "config\tag_registry.json"
)

REM Create Python path file for easy imports
echo import sys > portable_python_path.py
echo import os >> portable_python_path.py
echo. >> portable_python_path.py
echo # Add portable site-packages to Python path >> portable_python_path.py
echo script_dir = os.path.dirname(os.path.abspath(__file__)) >> portable_python_path.py
echo site_packages = os.path.join(script_dir, 'portable_python', 'site-packages') >> portable_python_path.py
echo if os.path.exists(site_packages) and site_packages not in sys.path: >> portable_python_path.py
echo     sys.path.insert(0, site_packages) >> portable_python_path.py

echo.
echo Portable installation complete!
echo.
echo Distribution contents:
echo ├── portable_python\       # Portable Python and packages
echo ├── src\                   # Application source code  
echo ├── config\                # Configuration files
echo └── start.bat             # Application launcher
echo.
echo Next steps:
echo 1. Configure your Google Sheets ID in config/config.json
echo 2. Set up Google API credentials (see GOOGLE_SHEETS_SETUP.md)
echo 3. Run start.bat to launch the application
echo.
echo This installation is now completely portable!
echo You can copy this entire folder to any Windows machine and it will work.
echo.
pause