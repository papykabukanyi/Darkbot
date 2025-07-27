#!/usr/bin/env python3
"""
Test script to verify credentials in the .env file.
"""

import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env
print("Loading environment variables from .env file...")
load_dotenv()

def test_mongodb_connection():
    """Test MongoDB connection."""
    print("\n=== Testing MongoDB Connection ===")
    try:
        # Get MongoDB connection details
        conn_str = os.getenv('MONGODB_CONNECTION_STRING')
        db_name = os.getenv('MONGODB_DATABASE')
        collection_name = os.getenv('MONGODB_COLLECTION')
        
        print(f"Connection string: {conn_str}")
        print(f"Database name: {db_name}")
        print(f"Collection name: {collection_name}")
        
        # Try to connect
        client = MongoClient(conn_str, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')  # Check if the server is responding
        
        # Get database and collection
        db = client[db_name]
        collection = db[collection_name]
        count = collection.count_documents({})
        
        print(f"✅ MongoDB connection successful!")
        print(f"✅ Connected to database: {db_name}")
        print(f"✅ Collection: {collection_name}")
        print(f"✅ Found {count} documents in the collection")
        return True
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False

def test_email_configuration():
    """Test email configuration."""
    print("\n=== Testing Email Configuration ===")
    try:
        # Get email configuration
        smtp_server = os.getenv('SMTP_HOST', os.getenv('EMAIL_SERVER', 'smtp.gmail.com'))
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        username = os.getenv('SMTP_USER', os.getenv('EMAIL_SENDER', ''))
        password = os.getenv('SMTP_PASS', os.getenv('EMAIL_PASSWORD', ''))
        recipients = os.getenv('EMAIL_RECIPIENTS', '').split(',')
        
        print(f"SMTP Server: {smtp_server}:{smtp_port}")
        print(f"Username: {username}")
        print(f"Recipients: {recipients}")
        
        # Try to connect to SMTP server
        smtp = smtplib.SMTP(smtp_server, smtp_port)
        smtp.starttls()
        smtp.login(username, password)
        
        print(f"✅ SMTP connection and login successful!")
        
        # Don't send an actual email - just test login
        smtp.quit()
        
        print(f"✅ Email configuration is valid")
        return True
    except Exception as e:
        print(f"❌ Email configuration failed: {e}")
        return False

def run_all_tests():
    """Run all tests."""
    print("=== Running Credential Tests ===")
    
    # Test MongoDB connection
    mongodb_ok = test_mongodb_connection()
    
    # Test email configuration
    email_ok = test_email_configuration()
    
    # Print summary
    print("\n=== Test Results ===")
    print(f"MongoDB Connection: {'✅ PASSED' if mongodb_ok else '❌ FAILED'}")
    print(f"Email Configuration: {'✅ PASSED' if email_ok else '❌ FAILED'}")
    
    if mongodb_ok and email_ok:
        print("\n✅ All credentials are working correctly!")
    else:
        print("\n❌ Some credentials failed verification. Check the errors above.")

if __name__ == "__main__":
    run_all_tests()
