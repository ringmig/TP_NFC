@echo off
REM Test portable Python setup

echo Testing Portable Python Setup
echo ================================

set "PORTABLE_PYTHON_DIR=%~dp0portable_python\windows"
set "PYTHON_EXECUTABLE=%PORTABLE_PYTHON_DIR%\python.exe"

echo.
echo Testing Python executable...
if exist "%PYTHON_EXECUTABLE%" (
    echo ✓ Python executable found: %PYTHON_EXECUTABLE%
    
    echo.
    echo Testing basic Python functionality...
    "%PYTHON_EXECUTABLE%" -c "print('✓ Python is working')" 2>nul
    if %errorlevel% neq 0 (
        echo ❌ Python basic test failed
        echo.
        echo Checking python313._pth file...
        if exist "%PORTABLE_PYTHON_DIR%\python313._pth" (
            echo Current python313._pth contents:
            type "%PORTABLE_PYTHON_DIR%\python313._pth"
        ) else (
            echo ❌ python313._pth file not found
        )
    ) else (
        echo.
        echo Testing imports...
        "%PYTHON_EXECUTABLE%" -c "import sys; print('✓ sys module works')" 2>nul
        "%PYTHON_EXECUTABLE%" -c "import os; print('✓ os module works')" 2>nul  
        "%PYTHON_EXECUTABLE%" -c "import site; print('✓ site module works')" 2>nul
        
        echo.
        echo Testing site-packages access...
        "%PYTHON_EXECUTABLE%" -c "import sys; print('Python paths:'); [print('  -', p) for p in sys.path]"
    )
) else (
    echo ❌ Python executable not found: %PYTHON_EXECUTABLE%
)

echo.
pause