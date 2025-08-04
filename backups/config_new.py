"""
Configuration file for the Sneaker Bot
"""

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from logging.handlers import RotatingFileHandler

# Base directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
LOG_DIR = os.path.join(BASE_DIR, 'logs')
CACHE_DIR = os.path.join(DATA_DIR, 'cache')

# Create directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# Logging configuration
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = os.path.join(LOG_DIR, 'sneakerbot.log')
LOG_MAX_SIZE = 5 * 1024 * 1024  # 5 MB
LOG_BACKUP_COUNT = 3

# Browser configuration
USE_SELENIUM = False  # Set to True to use Selenium for scraping
HEADLESS_BROWSER = True

# Proxy configuration
USE_PROXY = False
PROXY_CONFIG = {
    'proxy_file': os.path.join(DATA_DIR, 'proxies.json'),
    'max_fails': 3,
    'ban_time': 1800,  # 30 minutes
    'verify_proxies': True,
    'use_fallback': True
}

# Notification configuration
EMAIL_NOTIFICATIONS = True
EMAIL_SERVER = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_ADDRESS = 'your-email@gmail.com'  # Update this with your email
EMAIL_PASSWORD = 'your-app-password'    # Update this with your app password
EMAIL_RECIPIENT = 'your-email@gmail.com'  # Update this with recipient email
EMAIL_INTERVAL_MINUTES = 30

# Setup logging
def setup_logging():
    """Set up logging configuration."""
    logger = logging.getLogger("SneakerBot")
    logger.setLevel(LOG_LEVEL)
    
    # Clear existing handlers if any
    if logger.handlers:
        logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(formatter)
    
    # Create file handler
    file_handler = RotatingFileHandler(
        LOG_FILE, 
        maxBytes=LOG_MAX_SIZE, 
        backupCount=LOG_BACKUP_COUNT
    )
    file_handler.setLevel(LOG_LEVEL)
    file_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# Email function
def send_email(subject, body, recipients=None):
    """Send email notification."""
    if not EMAIL_NOTIFICATIONS:
        return False
    
    logger = logging.getLogger("SneakerBot")
    
    # Use the default recipient if none provided
    if not recipients:
        recipients = [EMAIL_RECIPIENT]
    elif isinstance(recipients, str):
        recipients = [recipients]
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = ', '.join(recipients)
    msg['Subject'] = subject
    
    # Attach body
    msg.attach(MIMEText(body, 'html'))
    
    try:
        # Connect to server
        server = smtplib.SMTP(EMAIL_SERVER, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        
        # Send email
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email sent successfully to {', '.join(recipients)}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False

# KicksOnFire configuration
KICKSONFIRE_CONFIG = {
    'name': 'KicksOnFire',
    'url': 'https://www.kicksonfire.com',
    'new_releases_url': 'https://www.kicksonfire.com/category/new-releases/',
    'upcoming_url': 'https://www.kicksonfire.com/category/upcoming-releases/all/',
    'rate_limit': 10  # Requests per minute
}

# StockX configuration
STOCKX_CONFIG = {
    'name': 'StockX',
    'type': 'stockx',
    'enabled': True,
    'url': 'https://stockx.com',
    'search_url': 'https://stockx.com/api/browse',
    'product_url': 'https://stockx.com/api/products',
    'use_proxy': USE_PROXY
}

# Profit checker configuration
PROFIT_CHECKER_CONFIG = {
    'data_sources': [STOCKX_CONFIG],
    'price_threshold': 20,  # Minimum profit percentage
    'fee_percentage': 12,   # Platform fees (e.g., StockX)
    'shipping_cost': 15,    # Average shipping cost
    'profit_margin_required': 20  # Min profit in dollars
}
