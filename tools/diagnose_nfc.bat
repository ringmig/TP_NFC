@echo off
echo Running NFC Diagnostic Tool...
echo.

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Please run install.bat first.
    pause
    exit /b 1
)

REM Ensure pyusb is installed
echo Ensuring pyusb is installed...
pip install pyusb > NUL 2>&1

REM Run the diagnostic
python tools\diagnose_nfc.py

pause