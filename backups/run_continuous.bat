@echo off
echo Darkbot Continuous Monitoring Mode
echo -------------------------------
echo.

:: Create a timestamp for log file
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
for /f "tokens=1-2 delims=: " %%a in ('time /t') do (set mytime=%%a%%b)
set timestamp=%mydate%_%mytime%
set log_file=darkbot_%timestamp%.log

:: Check if virtual environment exists
if not exist venv\Scripts\activate.bat (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Install requirements if needed
if not exist venv\Scripts\python.exe (
    echo Installing requirements...
    pip install -r requirements.txt
)

:: Run site verification first
echo Running site verification...
python utils\verify_sites.py --output "site_status_%timestamp%.txt"

:: Start the main bot in continuous mode with site verification
echo.
echo Starting Darkbot in continuous mode...
echo All output will be logged to %log_file%
echo.
echo Press Ctrl+C to stop the bot
echo.

python main.py --continuous --verify-sites --interval 90 --verbose --report-interval 1800 > %log_file% 2>&1

:: Deactivate virtual environment when done
call venv\Scripts\deactivate.bat

echo.
echo Bot stopped. Check %log_file% for details.
pause
