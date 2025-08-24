@echo off
echo Darkbot - StockX Price Checker
echo ===============================
echo.

:: Create required directories
if not exist logs mkdir logs
if not exist data mkdir data
if not exist data\cache mkdir data\cache

:: Activate virtual environment if it exists
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

echo.
echo Starting Darkbot...
echo.

:: Run the bot
python sneakerbot.py

:: Deactivate virtual environment if active
if defined VIRTUAL_ENV (
    call deactivate
)

pause
