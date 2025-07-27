"""
Simple test script to verify email settings.
Run this script to check if emails can be sent successfully.
"""

import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

def test_email_settings():
    print("Loading environment variables from .env file...")
    load_dotenv()
    
    # Get email settings from environment variables
    smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', '587'))
    
    # Try multiple environment variables for username/password
    smtp_user = os.environ.get('SMTP_USER')
    if not smtp_user:
        smtp_user = os.environ.get('EMAIL_FROM')
    if not smtp_user:
        smtp_user = os.environ.get('EMAIL_SENDER')
    
    smtp_pass = os.environ.get('SMTP_PASS')
    if not smtp_pass:
        smtp_pass = os.environ.get('EMAIL_PASSWORD')
    
    # Get recipient(s)
    recipients_str = os.environ.get('EMAIL_RECIPIENTS', '')
    recipients = [r.strip() for r in recipients_str.split(',') if r.strip()]
    
    print("Email Configuration:")
    print(f"SMTP Server: {smtp_host}:{smtp_port}")
    print(f"Username: {smtp_user}")
    print(f"Password: {'*' * len(smtp_pass) if smtp_pass else 'Not set'}")
    print(f"Recipients: {recipients}")
    
    if not smtp_user or not smtp_pass:
        print("ERROR: Username or password not set in environment variables!")
        sys.exit(1)
    
    if not recipients:
        print("ERROR: No recipients defined in EMAIL_RECIPIENTS!")
        sys.exit(1)
    
    print("\nTesting SMTP connection...")
    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            print("✅ SMTP login successful!")
            
            # Create a test message
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['Subject'] = "Darkbot Email Test"
            
            # Simple text content
            text = """
            This is a test email from your Darkbot application.
            
            If you're seeing this, your email configuration is working correctly!
            
            The bot will use this email configuration to send notifications about deals.
            """
            msg.attach(MIMEText(text, 'plain'))
            
            print("\nSending test email to:")
            for recipient in recipients:
                print(f"  - {recipient}")
                # Create a fresh message for each recipient
                msg_copy = MIMEMultipart()
                msg_copy['From'] = smtp_user
                msg_copy['Subject'] = "Darkbot Email Test"
                msg_copy['To'] = recipient
                msg_copy.attach(MIMEText(text, 'plain'))
                server.send_message(msg_copy)
            
            print("✅ Test email sent successfully!")
            print("\nYour email configuration is working correctly.")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure your email and password are correct")
        print("2. For Gmail, you need to use an App Password instead of your regular password")
        print("   To create an App Password:")
        print("   a. Go to your Google Account > Security")
        print("   b. Enable 2-Step Verification if not already enabled")
        print("   c. Go to App passwords > Create a new app password")
        print("3. Check that you have no typos in your SMTP host or port")
        sys.exit(1)

if __name__ == "__main__":
    test_email_settings()
