@echo off
echo Running Sneaker Bot with working scrapers only...
echo.

REM Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
    echo Virtual environment activated.
)

REM Run the bot with only working scrapers
python main.py --sites sneakers champssports footlocker idsports --mongodb

pause
