@echo off
echo Darkbot - StockX Price Checker Setup and Test

rem Create required directories and setup logging
echo Setting up project structure...
python setup_project.py

rem Fix Flask/Werkzeug compatibility issues
echo Fixing Flask dependencies...
call fix_flask_deps.bat

rem Run the StockX API test
echo Testing StockX API...
python test_stockx_api.py

echo Setup and test complete!
pause
