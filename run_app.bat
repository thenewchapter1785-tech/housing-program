@echo off
setlocal
cd /d "%~dp0"
set PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe
if not exist "%PYTHON_EXE%" (
    echo Python 3.12 was not found. Install it from https://www.python.org/downloads/windows/
    pause
    exit /b 1
)
"%PYTHON_EXE%" -m pip install -r requirements.txt >nul 2>&1
"%PYTHON_EXE%" src\main.py --menu
pause
