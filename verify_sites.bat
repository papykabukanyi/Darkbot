@echo off
echo Darkbot Site Verification Tool
echo ----------------------------
echo.

:: Create a timestamp for log file
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
for /f "tokens=1-2 delims=: " %%a in ('time /t') do (set mytime=%%a%%b)
set timestamp=%mydate%_%mytime%

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

:: Run site verification
echo Running site verification...
python utils\verify_sites.py --output "site_status_%timestamp%.txt" --verbose

:: Check if verification was successful
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo WARNING: Some sites are not available!
    echo Check the output file for details.
) else (
    echo.
    echo All sites are working properly!
)

:: Open the output file
echo.
echo Opening verification results...
start site_status_%timestamp%.txt

:: Deactivate virtual environment
call venv\Scripts\deactivate.bat

echo.
echo Done!
pause
