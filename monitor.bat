@echo off
echo Darkbot - Monitoring Script
echo ===========================

rem Create logs directory if it doesn't exist
if not exist logs mkdir logs

rem Activate the virtual environment if it exists
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

rem Run the monitoring script
python monitor.py %*

rem Check exit code
if %ERRORLEVEL% EQU 0 (
    echo All checks passed! System is healthy.
) else (
    echo Some checks failed. System may need attention!
)

rem Deactivate virtual environment if active
if defined VIRTUAL_ENV (
    call deactivate
)

pause
