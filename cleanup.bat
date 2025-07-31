@echo off
echo Cleaning up Darkbot codebase...

echo Creating backups directory if it doesn't exist
if not exist "backups" mkdir backups

echo Moving backup files to backups directory
move main_backup.py backups\ >nul 2>&1
move main_fixed.py backups\ >nul 2>&1
move main_improved.py backups\ >nul 2>&1
move main_restored.py backups\ >nul 2>&1

echo Creating tests directory if it doesn't exist
if not exist "tests" mkdir tests

echo Moving test files to tests directory
move test_webdriver.py tests\ >nul 2>&1
move test_webdriver_file.py tests\ >nul 2>&1
move proxy_test.py tests\ >nul 2>&1
move quick_email_test.py tests\ >nul 2>&1
move verify_fixes.py tests\ >nul 2>&1
move verify_credentials.py tests\ >nul 2>&1

echo Creating temp directory if it doesn't exist
if not exist "temp" mkdir temp

echo Cleaning up temporary files
del *.tmp >nul 2>&1
del *.log >nul 2>&1
del /s /q __pycache__\*.* >nul 2>&1

echo Cleanup complete!
echo.
echo Directory structure has been optimized:
echo - Main application files remain in root directory
echo - Backup files moved to backups/
echo - Test files moved to tests/
echo - Temporary files cleaned up
echo.
echo Next steps:
echo 1. Review the updated README.txt for new features
echo 2. Try the multi-source profit finder: run_profit_finder.bat
echo 3. Run all tests: run_all_tests.bat
echo.
