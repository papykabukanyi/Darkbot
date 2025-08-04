@echo off
echo ================================================
echo DARKBOT - RUN ALL TESTS
echo ================================================
echo.

:: Set Python executable path
set PYTHON_PATH=C:\Users\lovingtracktor\Desktop\Darkbot\.venv\Scripts\python.exe

:: Create logs directory if it doesn't exist
if not exist logs mkdir logs

echo Step 1: Testing StockX Scraper
echo ------------------------------
call test_stockx.bat
echo.

echo Step 2: Testing Adidas Scraper
echo ------------------------------
call test_adidas_scraper.bat
echo.

echo Step 3: Testing HTML Unescaping
echo ------------------------------
call test_html_unescape.bat
echo.

echo Step 4: Running Email Notification Test
echo ------------------------------
call test_email_notifications.bat
echo.

echo Step 5: All tests completed!
echo ================================================
echo.
echo You can now run the full application with:
echo   python main.py
echo.
echo Or monitor the application with:
echo   monitor_darkbot.bat
echo.
pause
