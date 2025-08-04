@echo off
echo Darkbot Production Monitoring Dashboard
echo ====================================

:: Set Python executable path
set PYTHON_PATH=C:\Users\lovingtracktor\Desktop\Darkbot\.venv\Scripts\python.exe

:: Check if python is available
if not exist %PYTHON_PATH% (
    echo Python executable not found at %PYTHON_PATH%
    echo Please install required dependencies or update the path in this script.
    goto :eof
)

:: Check for psutil and tabulate dependencies
%PYTHON_PATH% -c "import psutil, tabulate" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing required dependencies...
    %PYTHON_PATH% -m pip install psutil tabulate
)

:: Run the monitor script in watch mode
%PYTHON_PATH% monitor_darkbot.py --watch

pause
