@echo off
echo Darkbot - System Verification
echo ===========================
echo.
echo This script will verify that all essential components of Darkbot are working correctly.
echo.

rem Create logs directory if it doesn't exist
if not exist logs mkdir logs

rem Activate the virtual environment if it exists
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

rem Run the verification script
python verify_system.py

rem Check exit code
if %ERRORLEVEL% EQU 0 (
    echo.
    echo All verification checks passed! The system is ready to use.
) else (
    echo.
    echo Some verification checks failed. Please fix the issues before using the system.
)

rem Deactivate virtual environment if active
if defined VIRTUAL_ENV (
    call deactivate
)

pause
