@echo off
echo Darkbot - Essential Project Cleanup
echo ===============================
echo.
echo This script will clean up the most critical unnecessary files.
echo Backup copies will be stored in the 'backups' folder.
echo.
echo Press Ctrl+C to cancel, or
pause

:: Create backup directories if they don't exist
if not exist backups mkdir backups
if not exist backups\bak_files mkdir backups\bak_files
if not exist backups\old_configs mkdir backups\old_configs
if not exist backups\test_scripts mkdir backups\test_scripts

echo.
echo === Moving duplicate files to backup ===
echo.

:: Move backup and new files
move *.bak backups\bak_files\ 2>nul
move *.new backups\bak_files\ 2>nul

:: Move old config files (but keep config_fixed.py)
move config.py backups\old_configs\ 2>nul
move config_new.py backups\old_configs\ 2>nul
move simplified_config.py backups\old_configs\ 2>nul

:: Move unnecessary test scripts
move test_*.py backups\test_scripts\ 2>nul
move *_test.py backups\test_scripts\ 2>nul

:: Move old versions of main files
move main.py backups\bak_files\ 2>nul
move main_improved.py backups\bak_files\ 2>nul
move main_restored.py backups\bak_files\ 2>nul

:: Keep the most important test script
copy backups\test_scripts\test_stockx_api.py . 2>nul

echo.
echo === Cleanup complete! ===
echo.
echo The most critical cleanup has been completed.
echo You may now verify that the system is working correctly.
echo.
pause
