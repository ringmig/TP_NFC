@echo off
setlocal enabledelayedexpansion
REM TP_NFC Installation - Setup only (Python installed manually)

echo TP_NFC Installation - Setting up environment
echo ==========================================

REM Get script directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Set up directories - Python is already installed manually
set "PYTHON_DIR=%SCRIPT_DIR%python"
REM Standard Python site-packages location
set "STANDARD_SITE_PACKAGES_DIR=%PYTHON_DIR%\Lib\site-packages"

echo Checking for Python installation...
if not exist "%PYTHON_DIR%" (
    echo Error: Python directory not found at %PYTHON_DIR%
    echo Please manually install Python 3.13.5 to this directory:
    echo 1. Download python-3.13.5-amd64.exe from https://www.python.org/downloads/windows/
    echo 2. Run the installer
    echo 3. Choose 'Customize installation'
    echo 4. Set the installation location to: %PYTHON_DIR%
    echo 5. Make sure 'pip' is included in the installation
    echo 6. Make sure 'tcl/tk and IDLE' is included (for tkinter)
    echo.
    pause
    exit /b 1
)

REM Find python.exe
set "PYTHON_EXECUTABLE=%PYTHON_DIR%\python.exe"
if not exist "%PYTHON_EXECUTABLE%" (
    echo Error: Python executable not found at %PYTHON_EXECUTABLE%
    echo Please ensure Python is properly installed in the python directory.
    echo You might need to reinstall Python.
    pause
    exit /b 1
)

REM Test Python installation
echo Testing Python installation...
"%PYTHON_EXECUTABLE%" --version
if %errorlevel% neq 0 (
    echo ERROR: Python installation appears to be corrupted.
    pause
    exit /b 1
)

REM We will install packages to the STANDARD Python site-packages directory
REM No need to create a separate site-packages folder with --target
echo Standard Python site-packages directory: %STANDARD_SITE_PACKAGES_DIR%
if not exist "%STANDARD_SITE_PACKAGES_DIR%" (
    echo Error: Standard Python site-packages directory not found.
    echo This indicates a problem with the Python installation.
    pause
    exit /b 1
)

REM Upgrade pip and install dependencies to the STANDARD site-packages
echo Installing/upgrading pip...
"%PYTHON_EXECUTABLE%" -m pip install --upgrade pip

echo Installing requirements to standard Python site-packages...
if exist requirements.txt (
    "%PYTHON_EXECUTABLE%" -m pip install -r requirements.txt
    if !errorlevel! neq 0 (
        echo ERROR: Failed to install requirements from requirements.txt
        echo Please check the requirements.txt file and your internet connection.
        pause
        exit /b 1
    )
    echo Successfully installed packages from requirements.txt.
) else (
    echo No requirements.txt found, skipping dependency installation.
)

REM Create necessary application directories
echo Creating application directories...
if not exist "logs" mkdir "logs"
if not exist "config" mkdir "config"

REM Create tag registry file if it doesn't exist
if not exist "config\tag_registry.json" (
    echo {} > "config\tag_registry.json"
    echo Created default config\tag_registry.json
)

echo.
echo Setup complete!
echo Python directory: %PYTHON_DIR%
echo Packages installed to: %STANDARD_SITE_PACKAGES_DIR%
echo.
echo Next steps:
echo 1. Configure your Google Sheets ID in config/config.json
echo 2. Set up Google API credentials (see GOOGLE_SHEETS_SETUP.md)
echo 3. Run start.bat to launch the application
echo.
echo This installation is now set up!
echo.
pause