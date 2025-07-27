"""
Quick email test script - One time run to verify email settings.
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Email settings
# Get settings from environment variables
smtp_server = os.getenv('SMTP_HOST', 'smtp.gmail.com')
smtp_port = int(os.getenv('SMTP_PORT', '587'))
username = os.getenv('SMTP_USER', os.getenv('EMAIL_SENDER', ''))
password = os.getenv('SMTP_PASS', os.getenv('EMAIL_PASSWORD', ''))  # Use the app password from environment
recipients = os.getenv('EMAIL_RECIPIENTS', '').split(',')

# Create email
subject = "Darkbot Test Email - Please Ignore"
body = """
This is a test email from your Darkbot application.

If you're receiving this email, it means your email configuration is working correctly.
The bot will use this configuration to send you notifications about deals.

You don't need to reply to this message.
"""

print(f"Connecting to {smtp_server}:{smtp_port}...")
try:
    # Connect to server
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.ehlo()
        server.starttls()
        print(f"Logging in as {username}...")
        server.login(username, password)
        print("Login successful!")
        
        # Send to each recipient
        for recipient in recipients:
            print(f"Sending to {recipient}...")
            msg = MIMEMultipart()
            msg['From'] = username
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            server.send_message(msg)
            print(f"Email sent to {recipient}!")
    
    print("\nAll emails sent successfully!")
    print("Your email configuration is working properly.")

except Exception as e:
    print(f"Error: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure your app password is correct")
    print("2. Check that your email address is correct")
    print("3. Make sure Less secure app access is enabled if using a regular password")
