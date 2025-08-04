@echo off
rem This script will add the darkbot to the Windows startup programs

echo Setting up DarkBot to run at Windows startup...

rem Get the current directory
set "currentDir=%~dp0"
set "startupScript=%currentDir%auto_start.bat"
set "shortcutPath=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\DarkBot.lnk"

rem Create a shortcut in the Windows Startup folder
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\CreateShortcut.vbs"
echo sLinkFile = "%shortcutPath%" >> "%TEMP%\CreateShortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\CreateShortcut.vbs"
echo oLink.TargetPath = "%startupScript%" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.WorkingDirectory = "%currentDir%" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Description = "DarkBot Sneaker Scraper - Automatic Mode" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.IconLocation = "%SystemRoot%\System32\SHELL32.dll,21" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Save >> "%TEMP%\CreateShortcut.vbs"

cscript /nologo "%TEMP%\CreateShortcut.vbs"
del "%TEMP%\CreateShortcut.vbs"

echo.
echo DarkBot has been added to Windows startup!
echo The bot will now automatically start when you log in to Windows.
echo.
echo Do you want to start the bot now? (Y/N)
choice /C YN /M "Start the bot now"

if %ERRORLEVEL% EQU 1 (
    echo Starting the bot...
    start "" "%startupScript%"
) else (
    echo You can start the bot manually by running auto_start.bat
)

pause
