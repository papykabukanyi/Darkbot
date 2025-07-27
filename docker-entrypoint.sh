#!/bin/bash

# Darkbot Docker Run Script
# This script runs inside the Docker container

echo "=== Darkbot Starting ==="
date

# Check environment variables
echo "Checking environment variables..."
if [ -z "$MONGODB_CONNECTION_STRING" ]; then
  echo "Warning: MONGODB_CONNECTION_STRING is not set!"
fi

if [ -z "$EMAIL_NOTIFICATIONS" ] || [ "$EMAIL_NOTIFICATIONS" != "True" ]; then
  echo "Warning: EMAIL_NOTIFICATIONS is not enabled!"
fi

# Print email configuration
echo "Email configuration:"
echo "Server: $SMTP_HOST:$SMTP_PORT"
echo "From: $EMAIL_FROM"
echo "Recipients: $EMAIL_RECIPIENTS"
echo ""

# Check if we can connect to MongoDB
echo "Testing MongoDB connection..."
python -c "
import os, sys
try:
    from pymongo import MongoClient
    conn_str = os.environ.get('MONGODB_CONNECTION_STRING')
    if not conn_str:
        print('MongoDB connection string not set!')
        sys.exit(1)
    client = MongoClient(conn_str, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print('MongoDB connection successful!')
except Exception as e:
    print(f'MongoDB connection failed: {e}')
    sys.exit(1)
"

# If we get here, MongoDB is connected
echo "MongoDB connection successful!"

# Check if we can send email
echo "Testing email configuration..."
python -c "
import os, sys, smtplib
try:
    server = os.environ.get('SMTP_HOST')
    port = int(os.environ.get('SMTP_PORT', '587'))
    username = os.environ.get('SMTP_USER', os.environ.get('EMAIL_FROM'))
    password = os.environ.get('SMTP_PASS', os.environ.get('EMAIL_PASSWORD'))
    if not username or not password:
        print('Email credentials not configured properly!')
        sys.exit(1)
    with smtplib.SMTP(server, port) as smtp:
        smtp.starttls()
        smtp.login(username, password)
        print('SMTP login successful!')
except Exception as e:
    print(f'Email configuration test failed: {e}')
    sys.exit(1)
"

# If we get here, email is working
echo "Email configuration successful!"

# Run the bot with appropriate parameters
echo "Starting Darkbot..."
python main.py --continuous --interval 90 --verbose --mongodb --email
