#!/usr/bin/env python
"""
Test script to verify credentials are working.
"""

import os
import sys
import smtplib
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def test_mongodb():
    """Test MongoDB connection."""
    print("\n=== Testing MongoDB Connection ===")
    try:
        conn_str = os.getenv('MONGODB_CONNECTION_STRING')
        print(f"Connection string: {conn_str}")
        
        client = MongoClient(conn_str, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("MongoDB connection successful!")
        
        db_name = os.getenv('MONGODB_DATABASE', 'sneakerbot')
        coll_name = os.getenv('MONGODB_COLLECTION', 'deals')
        
        db = client[db_name]
        collection = db[coll_name]
        
        count = collection.count_documents({})
        print(f"Connected to database: {db_name}, collection: {coll_name}")
        print(f"Current document count: {count}")
        return True
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        return False

def test_email():
    """Test email configuration."""
    print("\n=== Testing Email Configuration ===")
    try:
        server = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        port = int(os.getenv('SMTP_PORT', '587'))
        username = os.getenv('SMTP_USER', os.getenv('EMAIL_FROM', ''))
        password = os.getenv('SMTP_PASS', os.getenv('EMAIL_PASSWORD', ''))
        
        print(f"Email server: {server}:{port}")
        print(f"Username: {username}")
        print(f"Password: {'*' * len(password) if password else 'Not set'}")
        
        smtp = smtplib.SMTP(server, port)
        smtp.starttls()
        smtp.login(username, password)
        print("SMTP login successful!")
        smtp.quit()
        return True
    except Exception as e:
        print(f"Email configuration test failed: {e}")
        return False

def main():
    """Main function."""
    print("=== Testing Credentials ===")
    
    # Test MongoDB
    mongo_success = test_mongodb()
    
    # Test email
    email_success = test_email()
    
    # Summary
    print("\n=== Test Summary ===")
    print(f"MongoDB: {'✓ PASS' if mongo_success else '✗ FAIL'}")
    print(f"Email:   {'✓ PASS' if email_success else '✗ FAIL'}")
    
    return 0 if mongo_success and email_success else 1

if __name__ == "__main__":
    sys.exit(main())
