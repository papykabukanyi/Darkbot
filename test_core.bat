@echo off
echo Darkbot - Core Functionality Test
echo ===============================
echo.
echo This script will test the core functionality of Darkbot.
echo.

:: Create required directories
if not exist logs mkdir logs
if not exist data mkdir data
if not exist data\cache mkdir data\cache

echo.
echo === Testing StockX API ===
echo.

:: Test StockX API connection
python -c "from utils.stockx_price_checker import StockXPriceChecker; checker = StockXPriceChecker(); print('StockX API initialized successfully')"

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to initialize StockX API
    echo Please check your .env file and ensure STOCKX_API_KEY, STOCKX_CLIENT_ID, and STOCKX_CLIENT_SECRET are set correctly.
    goto end
)

echo.
echo === Testing Configuration ===
echo.

:: Test configuration loading
python -c "from config_fixed import STOCKX_CONFIG; print('Configuration loaded successfully')"

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to load configuration
    echo Please check your config_fixed.py file.
    goto end
)

echo.
echo === Testing Core Files ===
echo.

:: Check if essential files exist
if not exist sneakerbot.py (
    echo ERROR: sneakerbot.py not found
    goto end
)

if not exist app.py (
    echo ERROR: app.py not found
    goto end
)

if not exist utils\stockx_adapter.py (
    echo ERROR: utils\stockx_adapter.py not found
    goto end
)

if not exist utils\stockx_price_checker.py (
    echo ERROR: utils\stockx_price_checker.py not found
    goto end
)

echo.
echo === All core functionality tests passed! ===
echo.
echo Your Darkbot installation appears to be working correctly.
echo.

:end
pause
