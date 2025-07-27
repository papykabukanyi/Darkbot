@echo off
REM Simple check script for Darkbot

echo === Darkbot System Check ===
echo.

REM Check Python version
echo Python version:
python --version
echo.

REM Check if requirements are installed
echo Checking requirements...
pip freeze | findstr /i pymongo
pip freeze | findstr /i requests
pip freeze | findstr /i selenium
pip freeze | findstr /i beautifulsoup4
echo.

REM Check MongoDB connection
echo Testing MongoDB connection...
python -c "import os, sys; from pymongo import MongoClient; try: conn_str = os.environ.get('MONGODB_CONNECTION_STRING', 'mongodb://localhost:27017'); client = MongoClient(conn_str, serverSelectionTimeoutMS=5000); client.admin.command('ping'); print('MongoDB connection successful!'); db = client[os.environ.get('MONGODB_DATABASE', 'sneakerbot')]; collection = db[os.environ.get('MONGODB_COLLECTION', 'deals')]; print(f'Connected to database: {db.name}, collection: {collection.name}'); print(f'Current document count: {collection.count_documents({})}')" || echo MongoDB connection failed

echo.

REM Check email configuration
echo Testing email configuration...
python -c "import os, sys, smtplib; try: server = os.environ.get('SMTP_HOST', 'smtp.gmail.com'); port = int(os.environ.get('SMTP_PORT', '587')); username = os.environ.get('SMTP_USER', os.environ.get('EMAIL_FROM', '')); password = os.environ.get('SMTP_PASS', os.environ.get('EMAIL_PASSWORD', '')); recipients = os.environ.get('EMAIL_RECIPIENTS', '').split(','); print(f'Email server: {server}:{port}'); print(f'Username: {username}'); print(f'Recipients: {recipients}'); smtp = smtplib.SMTP(server, port); smtp.starttls(); smtp.login(username, password); print('SMTP login successful!'); smtp.quit()" || echo Email configuration test failed

echo.
echo === System Check Complete ===

pause
