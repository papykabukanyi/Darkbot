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
    'sneakers': {
        'url': 'https://www.sneakers.com',
        'rate_limit': 10,  # seconds between requests
    },
    'champs': {
        'url': 'https://www.champssports.com',
        'rate_limit': 15,
    },
    'footlocker': {
        # Fixed URL typo: footlooker → footlocker
        'url': 'https://www.footlocker.com',
        'rate_limit': 12,
    },
    'idsports': {
        # Note: This might be intended for Hibbett/City Gear (formerly known as "Inspired Sports")
        # Updated to correct domain if possible
        'url': 'https://www.idsports.com',
        'rate_limit': 10,
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

# Notification settings
ENABLE_NOTIFICATIONS = True
EMAIL_NOTIFICATIONS = True
EMAIL_ADDRESS = 'papykabukanyi@gmail.com'
EMAIL_PASSWORD = 'lcqowjuwimhsptwq'
EMAIL_SERVER = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_RECIPIENT = 'papykabukanyi@gmail.com'
EMAIL_INTERVAL_MINUTES = 30

# Proxy settings (optional)
USE_PROXY = False
PROXIES = {
    'http': '',
    'https': '',
}

# Advanced
REQUEST_TIMEOUT = 30  # seconds
RETRY_ATTEMPTS = 3
CAPTCHA_DETECTION = True  # Try to detect if site is showing captcha
