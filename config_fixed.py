"""
Configuration file for the Sneaker Scraper Bot.
"""
import os
import logging
import random
from logging.handlers import RotatingFileHandler
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Directory setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, 'logs')
DATA_DIR = os.path.join(BASE_DIR, 'data')

# Ensure directories exist
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Logging configuration
LOG_FILE = os.path.join(LOG_DIR, 'sneakerbot.log')
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_MAX_SIZE = 5 * 1024 * 1024  # 5 MB
LOG_BACKUP_COUNT = 3

# Scraping settings
REQUEST_TIMEOUT = 30
RETRY_COUNT = 3
RETRY_DELAY = 5  # seconds

# Rate limiting (seconds between requests)
MIN_DELAY = 2
MAX_DELAY = 5

# User agent rotation
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
]

# Proxy settings (list of proxy URLs in format http://user:pass@host:port)
PROXIES = [
    # Add your proxies here
    # 'http://user:pass@host:port',
]

# Price comparison settings
RETAIL_MARKUP = 1.2  # 20% markup from retail price for profit calculation
MIN_PROFIT_MARGIN = 0.15  # 15% minimum profit margin

# Notification settings
ENABLE_NOTIFICATIONS = True

# Email notification settings
EMAIL_SERVER = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_ADDRESS = 'your_email@gmail.com'  # Replace with your email
EMAIL_PASSWORD = 'your_app_password'    # Replace with your app password
EMAIL_RECIPIENT = ['recipient@example.com']  # Replace with recipient email(s)

# KicksOnFire settings
KICKSONFIRE_URL = 'https://www.kicksonfire.com/app/'

# StockX settings
STOCKX_URL = 'https://stockx.com/'

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
    'use_proxy': False
}

# Profit checker configuration
PROFIT_CHECKER_CONFIG = {
    'data_sources': [STOCKX_CONFIG],
    'price_threshold': 20,  # Minimum profit percentage
    'fee_percentage': 12,   # Platform fees (e.g., StockX)
    'shipping_cost': 15,    # Average shipping cost
    'profit_margin_required': 20  # Min profit in dollars
}

def setup_logging(name=None):
    """Set up logging configuration."""
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    
    # Create a rotating file handler
    file_handler = RotatingFileHandler(
        LOG_FILE, 
        maxBytes=LOG_MAX_SIZE, 
        backupCount=LOG_BACKUP_COUNT
    )
    file_handler.setLevel(LOG_LEVEL)
    
    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)
    
    # Create a formatter and set it for both handlers
    formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def get_random_user_agent():
    """Return a random user agent from the list."""
    return random.choice(USER_AGENTS)


def get_random_proxy():
    """Return a random proxy from the list or None if no proxies are configured."""
    if not PROXIES:
        return None
    return random.choice(PROXIES)


def get_random_delay():
    """Return a random delay between MIN_DELAY and MAX_DELAY."""
    return random.uniform(MIN_DELAY, MAX_DELAY)


def send_email(subject, body, html=False):
    """
    Send an email notification.
    
    Args:
        subject (str): Email subject
        body (str): Email body
        html (bool): Whether the body is HTML or not
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    if not ENABLE_NOTIFICATIONS:
        return False
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"[SneakerBot] {subject}"
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = ', '.join(EMAIL_RECIPIENT) if isinstance(EMAIL_RECIPIENT, list) else EMAIL_RECIPIENT
        
        if html:
            content = MIMEText(body, 'html')
        else:
            content = MIMEText(body, 'plain')
        
        msg.attach(content)
        
        server = smtplib.SMTP(EMAIL_SERVER, EMAIL_PORT)
        server.starttls()
        
        if EMAIL_ADDRESS and EMAIL_PASSWORD:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        
        recipients = EMAIL_RECIPIENT if isinstance(EMAIL_RECIPIENT, list) else [EMAIL_RECIPIENT]
        server.sendmail(
            EMAIL_ADDRESS,
            recipients,
            msg.as_string()
        )
        server.quit()
        return True
    except Exception as e:
        logger = setup_logging('email')
        logger.error(f"Failed to send email: {str(e)}")
        return False
