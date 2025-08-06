@echo off
rem StockX CLI runner
echo StockX Price Checker CLI

rem Activate the virtual environment if it exists
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Please run setup_and_test.bat first.
    exit /b 1
)

rem Run the CLI script with all arguments passed through
python stockx_cli.py %*

rem Deactivate virtual environment
call .venv\Scripts\deactivate.bat
