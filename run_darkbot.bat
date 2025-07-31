@echo off
echo ================================================
echo DARKBOT - SNEAKER DEAL FINDER
echo ================================================
echo.

:: Set Python executable path
set PYTHON_PATH=C:\Users\lovingtracktor\Desktop\Darkbot\.venv\Scripts\python.exe

:: Create logs directory if it doesn't exist
if not exist logs mkdir logs

:: Set timestamp for log file
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set datetime=%%a
set log_date=%datetime:~0,8%
set log_time=%datetime:~8,6%
set LOGFILE=logs\darkbot_%log_date%_%log_time%.log

echo Running Darkbot with common settings:
echo - All default sites
echo - Email notifications enabled
echo - MongoDB storage enabled
echo - Continuous mode (runs every 30 min)
echo.
echo Log will be saved to: %LOGFILE%
echo.
echo Press Ctrl+C to stop the process at any time.
echo.

%PYTHON_PATH% main.py --email --continuous > %LOGFILE% 2>&1

pause
