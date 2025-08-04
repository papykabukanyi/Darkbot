@echo off
echo Streamlined SneakerBot - Profitable Sneaker Finder
echo =================================================

REM Check if config_fixed.py exists, if not, rename it
if not exist config_fixed.py (
    echo Renaming config_fixed.py to config.py
    copy config_fixed.py config.py
)

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo No virtual environment found. Using system Python.
)

REM Run the sneakerbot with profit checking and notifications
echo Running SneakerBot in continuous mode (will keep running until you close this window)...
python sneakerbot.py --check-profit --notify --interval 30

REM Pause to see results
pause
