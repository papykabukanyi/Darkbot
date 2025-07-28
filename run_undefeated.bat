@echo off
echo ===================================
echo Darkbot - Undefeated Edition Launcher
echo ===================================
echo.

REM Activate virtual environment if it exists
if exist .venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo No virtual environment found, using system Python.
)

REM Check for Python
python --version > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python not found! Please install Python 3.8 or higher.
    goto :exit
)

REM Check if requirements need to be installed
echo Checking dependencies...
python -c "import requests, bs4, selenium, colorama, schedule, pymongo" > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Installing required packages...
    pip install -r requirements.txt
)

REM Start the bot
echo.
echo Starting Darkbot with Undefeated focus...
echo Log file will be created in the current directory.
echo Press Ctrl+C to stop the bot.
echo.

REM Create a timestamp for the log file
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "logfile=darkbot_undefeated_%dt:~0,8%_%dt:~8,6%.log"

REM Run the bot and save output to log file
python run_with_undefeated.py --interval 30 | tee "%logfile%"

:exit
pause
