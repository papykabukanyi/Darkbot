@echo off
echo ===== DARKBOT SNEAKER SCRAPER =====
echo This is the fixed version of the bot.

REM Set up logging to a file
set LOG_FILE=darkbot_run_%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log
set LOG_FILE=%LOG_FILE: =0%

echo Starting bot run at %date% %time% > %LOG_FILE%
echo Log will be saved to: %LOG_FILE%
echo.

echo Running bot with all default sites...
echo ---------------------------------
python main.py --verbose >> %LOG_FILE% 2>&1

echo Bot run complete!
echo Check the log file for details: %LOG_FILE%
echo.
echo Press any key to view the log file...
pause > nul

type %LOG_FILE%
echo.
echo Press any key to exit...
pause > nul
