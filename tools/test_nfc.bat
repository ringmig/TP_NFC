@echo off
echo Running NFC Test...
echo.

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Please run install.bat first.
    pause
    exit /b 1
)

REM Run the test
python tools\test_nfc.py

pause