@echo off
REM Launch application hidden using PowerShell
powershell -WindowStyle Hidden -Command "& { Set-Location '%~dp0'; .\venv\Scripts\Activate.ps1; python src\main.py }"
