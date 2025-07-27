#!/bin/bash

# Simple check script for Darkbot
echo "=== Darkbot System Check ==="
echo

# Check Python version
echo "Python version:"
python --version
echo

# Check if requirements are installed
echo "Checking requirements..."
pip freeze | grep -i pymongo
pip freeze | grep -i requests
pip freeze | grep -i selenium
pip freeze | grep -i beautifulsoup4
echo

# Check MongoDB connection
echo "Testing MongoDB connection..."
python -c "
import os
import sys
try:
    from pymongo import MongoClient
    conn_str = os.environ.get('MONGODB_CONNECTION_STRING', 'mongodb://mongo:SMhYDmJOIDZMrHqHhVJRIHzxcOfJUaNr@shortline.proxy.rlwy.net:51019')
    client = MongoClient(conn_str, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print('MongoDB connection successful!')
    db = client[os.environ.get('MONGODB_DATABASE', 'sneakerbot')]
    collection = db[os.environ.get('MONGODB_COLLECTION', 'deals')]
    print(f'Connected to database: {db.name}, collection: {collection.name}')
    print(f'Current document count: {collection.count_documents({})}')
except Exception as e:
    print(f'MongoDB connection failed: {e}')
    sys.exit(1)
"
echo

# Check email configuration
echo "Testing email configuration..."
python -c "
import os
import sys
import smtplib
try:
    server = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    port = int(os.environ.get('SMTP_PORT', '587'))
    username = os.environ.get('SMTP_USER', os.environ.get('EMAIL_FROM', ''))
    password = os.environ.get('SMTP_PASS', os.environ.get('EMAIL_PASSWORD', ''))
    recipients = os.environ.get('EMAIL_RECIPIENTS', '').split(',')
    
    if not username or not password:
        print('Email credentials not configured')
        sys.exit(0)
        
    print(f'Email server: {server}:{port}')
    print(f'Username: {username}')
    print(f'Recipients: {recipients}')
    
    with smtplib.SMTP(server, port) as smtp:
        smtp.starttls()
        smtp.login(username, password)
        print('SMTP login successful!')
except Exception as e:
    print(f'Email configuration test failed: {e}')
    sys.exit(1)
"

echo
echo "=== System Check Complete ==="
