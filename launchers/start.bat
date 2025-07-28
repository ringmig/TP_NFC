@echo off
setlocal
REM TP_NFC Application Launcher - Portable Version

REM Get the directory where this script is located (launchers folder)
set "LAUNCHER_DIR=%~dp0"
REM Get the project root (TP_NFC folder) - parent of launchers
set "PROJECT_DIR=%LAUNCHER_DIR%.."

REM Change to the project root directory
cd /d "%PROJECT_DIR%"

REM Define paths relative to the current directory (which is now PROJECT_DIR)
set "PYTHON_DIR=python"
set "PYTHON_EXECUTABLE=python\python.exe"
set "SITE_PACKAGES_DIR=python\site-packages"

REM Check if Python executable exists
if not exist "%PYTHON_EXECUTABLE%" (
    echo Error: Python executable not found at %PYTHON_EXECUTABLE%
    echo Please run install.bat first to set up the environment.
    pause
    exit /b 1
)

REM Check if main.py exists in src
if not exist "src\main.py" (
    echo Error: src\main.py not found.
    echo Please ensure you are running this from the correct location.
    pause
    exit /b 1
)

REM Set PYTHONPATH to include our local site-packages and src directory
set PYTHONPATH=%CD%\python\site-packages;%CD%\src;%PYTHONPATH%

REM Try to run hidden with PowerShell, fallback to minimized if not available
powershell -WindowStyle Hidden -Command "& { cd '%CD%'; $env:PYTHONPATH='%CD%\python\site-packages;%CD%\src'; & '.\python\python.exe' 'src\main.py' }" 2>nul
if %errorlevel% neq 0 (
    REM PowerShell not available, use start /min for minimized window
    echo PowerShell not found, launching minimized...
    start /min "" python\python.exe src\main.py
)