@echo off
REM Darkbot Run Script - Fixed version

echo === Starting Darkbot ===
echo Current date: %date% %time%

REM Check if main.py exists
if not exist main.py (
    echo ERROR: main.py not found! Make sure you're in the correct directory.
    pause
    exit /b 1
)

REM Load environment variables from .env file
echo Loading environment variables...
python -c "from dotenv import load_dotenv; load_dotenv(); print('Environment loaded successfully')"

echo.
echo SMTP Settings:
echo Server: smtp.gmail.com:587
echo Username: papykabukanyi@gmail.com
echo Recipients: papykabukanyi@gmail.com, hoopstar385@gmail.com
echo.

echo Starting Darkbot in continuous mode...
echo The bot will run continuously and send email notifications.
echo Press Ctrl+C to stop the bot.
echo.

REM Run the bot with the correct parameters
python main.py --continuous --interval 90 --verbose --mongodb --email

pause
