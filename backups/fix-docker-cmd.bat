@echo off
REM Quick Fix for Dockerfile CMD arguments

echo Fixing Dockerfile CMD arguments...

REM Update the Dockerfile
powershell -Command "(Get-Content Dockerfile) -replace 'CMD \[\"python\", \"main.py\", \"--continuous\", \"--verify-sites\", \"--interval\", \"90\", \"--verbose\", \"--report-interval\", \"1800\"\]', 'CMD [\"python\", \"main.py\", \"--continuous\", \"--interval\", \"90\", \"--verbose\", \"--mongodb\", \"--email\"]' | Set-Content Dockerfile.new"
move /Y Dockerfile.new Dockerfile

echo Dockerfile updated with correct command arguments.
echo New command: python main.py --continuous --interval 90 --verbose --mongodb --email
echo.
echo To deploy:
echo 1. Commit these changes
echo 2. Push to your repository
echo 3. Deploy on Railway
echo.
echo Press any key to continue...
pause > nul
