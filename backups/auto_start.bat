@echo off
title DarkBot Sneaker Scraper - Automatic Mode
echo ====================================================
echo DarkBot Sneaker Scraper - Starting in Automatic Mode
echo ====================================================
echo.

rem Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python and try again.
    pause
    exit /b 1
)

rem Check if virtual environment exists, create if not
if not exist .venv (
    echo Creating Python virtual environment...
    python -m venv .venv
    if %ERRORLEVEL% neq 0 (
        echo Error: Failed to create virtual environment.
        pause
        exit /b 1
    )
)

rem Activate virtual environment
call .venv\Scripts\activate
if %ERRORLEVEL% neq 0 (
    echo Error: Failed to activate virtual environment.
    pause
    exit /b 1
)

rem Install or upgrade required packages
echo Installing required packages...
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo Warning: Some packages may have failed to install.
)

rem Create log directory if it doesn't exist
if not exist logs mkdir logs

rem Get current date and time for log file
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set logfile=logs\darkbot_%datetime:~0,8%_%datetime:~8,6%.log

echo Starting bot in continuous mode with 30-minute intervals...
echo Bot output will be logged to: %logfile%
echo.
echo The bot is now running! You can minimize this window.
echo It will automatically check for deals every 30 minutes
echo and send emails to configured recipients.
echo.
echo Press Ctrl+C to stop the bot.
echo.

rem Run the bot in continuous mode with 30-minute intervals
python main.py --continuous --interval 30 --verbose > %logfile% 2>&1

pause
