@echo off
echo Darkbot - Project Cleanup Utility
echo ===============================
echo.
echo This script will clean up unnecessary files and organize the project.
echo Backup copies will be stored in the 'backups' folder.
echo.
echo Press Ctrl+C to cancel, or
pause

:: Create backup directories if they don't exist
if not exist backups mkdir backups
if not exist backups\scripts mkdir backups\scripts
if not exist backups\python_files mkdir backups\python_files
if not exist backups\config mkdir backups\config
if not exist backups\docker mkdir backups\docker
if not exist backups\docs mkdir backups\docs

echo.
echo === Moving duplicate and test scripts to backup ===
echo.

:: Move duplicate/older scripts to backup
move main.py.new backups\python_files\ 2>nul
move main.py.bak backups\python_files\ 2>nul
move sneakerbot.py.bak backups\python_files\ 2>nul
move sneakerbot.py.new backups\python_files\ 2>nul
move __init__.py.new backups\python_files\ 2>nul
move .env.bak backups\config\ 2>nul
move .env.template backups\config\ 2>nul

:: Move test scripts to backup
move test.py backups\python_files\ 2>nul
move test_*.py backups\python_files\ 2>nul
move *_test.py backups\python_files\ 2>nul
move test_*.bat backups\scripts\ 2>nul
move verify_*.py backups\python_files\ 2>nul
move verify_*.bat backups\scripts\ 2>nul
move run_tests.py backups\python_files\ 2>nul

:: Keep specific test files that might be needed
copy backups\python_files\test_stockx_api.py . 2>nul

echo.
echo === Moving unused configuration files to backup ===
echo.

:: Move unused config files
move config_new.py backups\config\ 2>nul
move simplified_config.py backups\config\ 2>nul
move config.py backups\config\ 2>nul

:: Move docker files to backup if not using Docker
echo Do you want to keep Docker configuration files? (Y/N)
set /p keepdocker=
if /i "%keepdocker%"=="N" (
    move docker-compose.yml backups\docker\ 2>nul
    move docker-entrypoint.sh backups\docker\ 2>nul
    move docker-healthcheck.sh backups\docker\ 2>nul
    move Dockerfile backups\docker\ 2>nul
    move DOCKER_DEPLOYMENT.md backups\docs\ 2>nul
)

echo.
echo === Moving documentation files to a central location ===
echo.

:: Create docs directory if it doesn't exist
if not exist docs mkdir docs

:: Move all markdown files to docs
move *.md docs\ 2>nul
:: But keep README.md in the root
copy docs\README.md . 2>nul

echo.
echo === Cleaning up duplicate runner scripts ===
echo.

:: Keep only necessary runner scripts
move run_*.bat backups\scripts\ 2>nul
:: Keep important ones
copy backups\scripts\run_bot.bat . 2>nul
copy backups\scripts\run_darkbot.bat . 2>nul

echo.
echo === Creating minimal set of important files ===
echo.

:: Create a simple starter batch file if it doesn't exist
if not exist start.bat (
    echo @echo off > start.bat
    echo echo Starting Darkbot... >> start.bat
    echo. >> start.bat
    echo :: Create required directories >> start.bat
    echo if not exist logs mkdir logs >> start.bat
    echo if not exist data mkdir data >> start.bat
    echo if not exist data\cache mkdir data\cache >> start.bat
    echo. >> start.bat
    echo :: Activate virtual environment if it exists >> start.bat
    echo if exist .venv\Scripts\activate.bat ( >> start.bat
    echo     call .venv\Scripts\activate.bat >> start.bat
    echo ) >> start.bat
    echo. >> start.bat
    echo :: Start the bot >> start.bat
    echo python sneakerbot.py >> start.bat
    echo. >> start.bat
    echo pause >> start.bat
    echo Created new start.bat file
)

echo.
echo === Cleaning up complete! ===
echo.
echo Unnecessary files have been moved to the 'backups' folder.
echo Documentation has been centralized in the 'docs' folder.
echo.
echo Project structure is now organized and minimal.
echo.
pause
