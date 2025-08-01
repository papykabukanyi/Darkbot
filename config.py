"""
Configuration settings for the sneaker bot.
"""

import os
import logging
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Set up logging
logger = logging.getLogger("Config")

# Target websites
WEBSITES = {
    'footlocker': {
        'url': 'https://www.footlocker.com',
        'rate_limit': 12,  # seconds between requests
    },
    'eastbay': {
        'url': 'https://www.eastbay.com',
        'rate_limit': 15,
    },
    'finishline': {
        'url': 'https://www.finishline.com',
        'rate_limit': 15,
    },
    'jdsports': {
        'url': 'https://www.jdsports.com',
        'rate_limit': 15,
    },
    'champssports': {
        'url': 'https://www.champssports.com',
        'rate_limit': 12,
    },
    'hibbett': {
        'url': 'https://www.hibbett.com',
        'rate_limit': 10,
    },
    'nike': {
        'url': 'https://www.nike.com',
        'rate_limit': 20,
    },
    'adidas': {
        'url': 'https://www.adidas.com',
        'rate_limit': 18,
    },
    'footaction': {
        'url': 'https://www.footaction.com',
        'rate_limit': 12,
    },
    'snipes': {
        'url': 'https://www.snipesusa.com',
        'rate_limit': 15,
    },
    'stadiumgoods': {
        'url': 'https://www.stadiumgoods.com',
        'rate_limit': 15,
    },
    'dtlr': {
        'url': 'https://www.dtlr.com',
        'rate_limit': 12,
    }
}

# Default request headers to mimic a browser
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# Scraping settings
USE_SELENIUM = True  # Set to False to use only requests (faster but less reliable for dynamic sites)
HEADLESS_BROWSER = True  # Run browser in headless mode (no GUI)

# Product filters
MIN_DISCOUNT_PERCENT = 30  # Only consider products with at least this discount
BRANDS_OF_INTEREST = [
    'Nike',
    'Adidas',
    'Jordan',
    'Puma',
    'New Balance',
    'Reebok',
    'Asics',
    'Vans',
    'Converse',
    'Under Armour'
]

# Data storage
SAVE_TO_CSV = True
CSV_FILENAME = 'sneaker_deals.csv'
DATABASE_ENABLED = False
DATABASE_PATH = 'deals.db'

# MongoDB settings
MONGODB_ENABLED = True
MONGODB_CONNECTION_STRING = os.getenv('MONGODB_CONNECTION_STRING', 'mongodb://localhost:27017')
MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'sneakerbot')
MONGODB_COLLECTION = os.getenv('MONGODB_COLLECTION', 'deals')

# Notification settings
ENABLE_NOTIFICATIONS = True
EMAIL_NOTIFICATIONS = os.getenv('EMAIL_NOTIFICATIONS', 'True').lower() == 'true'
# Use SMTP config from environment variables
EMAIL_SERVER = os.getenv('SMTP_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('SMTP_PORT', '587'))
EMAIL_ADDRESS = os.getenv('SMTP_USER', os.getenv('EMAIL_SENDER', ''))
EMAIL_PASSWORD = os.getenv('SMTP_PASS', os.getenv('EMAIL_PASSWORD', ''))
EMAIL_RECIPIENT = os.getenv('EMAIL_RECIPIENTS', '')
EMAIL_INTERVAL_MINUTES = int(os.getenv('EMAIL_INTERVAL_MINUTES', '30'))

# Proxy settings
USE_PROXY = True
PROXY_CONFIG = {
    'proxy_file': 'proxies.json',       # File to store proxy list
    'max_fails': 3,                      # Maximum failures before banning a proxy
    'ban_time': 1800,                    # Ban time in seconds (30 minutes)
    'verify_on_startup': True,           # Verify proxies when starting
    'auto_fetch_free': True,             # Fetch free proxies if none available
    'rotation_strategy': 'round-robin',  # Rotation strategy (round-robin, performance, random)
    'captcha_detection': True            # Enable CAPTCHA detection
}

# Advanced
REQUEST_TIMEOUT = 30  # seconds
RETRY_ATTEMPTS = 3
CAPTCHA_DETECTION = True  # Try to detect if site is showing captcha
