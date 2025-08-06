@echo off
echo Starting Darkbot StockX Price Checker...

rem Activate the virtual environment if it exists
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
    echo Virtual environment activated.
) else (
    echo Virtual environment not found. Creating one...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo Installing requirements...
    pip install -r requirements.txt
)

rem Create required directories
if not exist logs mkdir logs
if not exist data\cache mkdir data\cache

rem Run the main script with any provided arguments
echo Running StockX Price Checker...
python sneakerbot.py %*

rem Deactivate virtual environment
call .venv\Scripts\deactivate.bat
echo Done.
