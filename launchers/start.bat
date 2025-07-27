@echo off
REM TP_NFC Portable Application Launcher for Windows

REM Get script directory and go to parent (project root)
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."
cd /d "%PROJECT_DIR%"

REM Check for portable Python first
set "PORTABLE_PYTHON_DIR=%PROJECT_DIR%\portable_python\windows"
set "PYTHON_EXECUTABLE="
set "SITE_PACKAGES_DIR=%PROJECT_DIR%\portable_python\site-packages"

if exist "%PORTABLE_PYTHON_DIR%\python.exe" (
    set "PYTHON_EXECUTABLE=%PORTABLE_PYTHON_DIR%\python.exe"
) else (
    REM Check for system Python
    python --version >nul 2>&1
    if %errorlevel% equ 0 (
        set "PYTHON_EXECUTABLE=python"
    ) else (
        echo Error: No Python installation found. Please run install.bat first.
        pause
        exit /b 1
    )
)

REM Check if site-packages directory exists
if not exist "%SITE_PACKAGES_DIR%" (
    echo Error: Portable packages not found. Please run install.bat first.
    pause
    exit /b 1
)

REM Check if main.py exists
if not exist "src\main.py" (
    echo Error: src\main.py not found. Please ensure you're in the correct directory.
    pause
    exit /b 1
)

REM Set Python path to include portable packages
set "PYTHONPATH=%SITE_PACKAGES_DIR%;%PYTHONPATH%"

REM Launch application hidden using PowerShell with portable Python path
powershell -WindowStyle Hidden -Command "& { 
    Set-Location '%PROJECT_DIR%'; 
    $env:PYTHONPATH='%SITE_PACKAGES_DIR%;' + $env:PYTHONPATH; 
    & '%PYTHON_EXECUTABLE%' -c \"
import portable_python_path
import sys
import os
# Add src directory to path
src_dir = os.path.join(os.getcwd(), 'src')
sys.path.insert(0, src_dir)
import main
main.main()
\" 
}"