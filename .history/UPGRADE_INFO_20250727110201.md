# DarkBot Upgrade - July 2025

The bot has been significantly improved with the following changes:

## 1. Security Enhancements

- All sensitive API keys and credentials have been moved to a `.env` file
- Added `.gitignore` file to prevent accidental exposure of secrets
- Environment variables are now loaded with python-dotenv

## 2. Email Notification Improvements

- Email notifications now send to multiple recipients:
  - papykabukanyi@gmail.com
  - hoopstar385@gmail.com
- Configured to send updates every 30 minutes
- Enhanced email templates with better formatting

## 3. Automatic Startup

- Added `auto_start.bat` that sets up and runs the bot automatically
- Created `setup_autostart.bat` to add the bot to Windows startup programs
- Bot now runs in continuous mode by default, checking every 30 minutes

## 4. Configuration Changes

- MongoDB is now enabled by default for better deal tracking
- All configuration is loaded from environment variables where appropriate
- Added better logging to troubleshoot any issues

## 5. How to Use the New Features

1. Run `setup_autostart.bat` once to make the bot start automatically with Windows
2. Configure your email settings in the `.env` file
3. The bot will automatically check for deals every 30 minutes
4. Both email addresses will receive notifications about deals found

## Note About Email Settings

To use Gmail for sending notifications:
1. You need to use an "App Password" rather than your regular Google password
2. Go to your Google Account → Security → 2-Step Verification → App Passwords
3. Create a new app password for "Mail" and use that in the .env file

Enjoy your upgraded DarkBot!
