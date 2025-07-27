@echo off
echo Darkbot Proxy Manager
echo =====================

echo Checking Python installation...
python --version > NUL 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python not found. Please install Python 3.8 or newer.
    pause
    exit /b 1
)

echo Setting up virtual environment...
if not exist .venv (
    python -m venv .venv
)
call .venv\Scripts\activate

echo Installing requirements...
pip install -r requirements.txt

echo.
echo Proxy Management System
echo ======================
echo [1] Initialize proxy system
echo [2] Fetch free proxies
echo [3] Add proxies from file
echo [4] Test proxy configuration
echo [5] Enable proxy system in config
echo [6] Disable proxy system in config
echo [7] Exit
echo.

set /p choice="Enter your choice (1-7): "

if "%choice%"=="1" (
    echo Initializing proxy system...
    python proxy_manager.py init
) else if "%choice%"=="2" (
    echo Fetching free proxies...
    python proxy_manager.py fetch
) else if "%choice%"=="3" (
    set /p file="Enter path to proxy list file: "
    python proxy_manager.py add %file%
) else if "%choice%"=="4" (
    echo Testing proxy configuration...
    python proxy_test.py test
    echo.
    echo Press any key to continue testing with CAPTCHA detection...
    pause > NUL
    python proxy_test.py test --captcha
) else if "%choice%"=="5" (
    echo Enabling proxy system in config...
    powershell -Command "(Get-Content config.py) -replace '# Proxy settings\r\nUSE_PROXY = False', '# Proxy settings\r\nUSE_PROXY = True' | Set-Content config.py"
    echo Proxy system enabled.
) else if "%choice%"=="6" (
    echo Disabling proxy system in config...
    powershell -Command "(Get-Content config.py) -replace '# Proxy settings\r\nUSE_PROXY = True', '# Proxy settings\r\nUSE_PROXY = False' | Set-Content config.py"
    echo Proxy system disabled.
) else if "%choice%"=="7" (
    echo Exiting...
    exit /b 0
) else (
    echo Invalid choice.
)

echo.
pause
