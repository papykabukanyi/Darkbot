"""
Main configuration file for the Sneaker Bot.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# List of shoe brands we're interested in
BRANDS_OF_INTEREST = [
    'Nike', 'Adidas', 'Jordan', 'Yeezy', 'New Balance', 
    'Asics', 'Reebok', 'Puma', 'Under Armour', 'Converse'
]

# Minimum discount percentage to consider a deal
MIN_DISCOUNT_PERCENT = 20

# Browser settings
HEADLESS_BROWSER = True
USE_SELENIUM = True
SCREENSHOT_ON_ERROR = False

# CSV Export settings
SAVE_TO_CSV = True
CSV_FILENAME = "sneaker_deals.csv"

# Database settings
DATABASE_ENABLED = True
DATABASE_PATH = "sneaker_deals.db"

# Email notification settings
EMAIL_NOTIFICATIONS = True
EMAIL_INTERVAL_MINUTES = 30

# Email server settings
EMAIL_SERVER = os.getenv('SMTP_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('SMTP_PORT', '587'))
EMAIL_ADDRESS = os.getenv('SMTP_USER', os.getenv('EMAIL_SENDER', ''))
EMAIL_PASSWORD = os.getenv('SMTP_PASS', os.getenv('EMAIL_PASSWORD', ''))
EMAIL_RECIPIENT = os.getenv('EMAIL_RECIPIENTS', '')

# MongoDB settings
MONGODB_ENABLED = True  # Set to True to enable MongoDB storage
MONGODB_CONNECTION_STRING = "mongodb://localhost:27017"  # Set this in your .env file, not here
MONGODB_DATABASE = "sneaker_deals"
MONGODB_COLLECTION = "deals"

# Cloudflare R2 settings (Legacy - replaced by MongoDB)
CLOUDFLARE_R2_ENABLED = False  # Set to True to enable R2 storage
CLOUDFLARE_R2_ACCESS_KEY = ""  # Set this in your .env file, not here
CLOUDFLARE_R2_SECRET_KEY = ""  # Set this in your .env file, not here
CLOUDFLARE_R2_ENDPOINT = ""    # Your Cloudflare R2 endpoint URL
CLOUDFLARE_R2_BUCKET = "sneaker-deals"  # Your Cloudflare R2 bucket name

# Proxy settings
USE_PROXY = True
PROXY_CONFIG = {
    'proxy_file': 'proxies.json',       # File to store proxy list
    'max_fails': 3,                      # Maximum failures before banning a proxy
    'ban_time': 1800,                    # Ban time in seconds (30 minutes)
    'verify_proxies': True,              # Verify proxies on startup
    'use_fallback': True                 # Use fallback system when no proxies available
}

# Cloudflare R2 settings
CLOUDFLARE_R2_ENABLED = False
CLOUDFLARE_R2_ACCESS_KEY = "your_access_key"  # Replace with your Cloudflare R2 access key
CLOUDFLARE_R2_SECRET_KEY = "your_secret_key"  # Replace with your Cloudflare R2 secret key
CLOUDFLARE_R2_ENDPOINT = "https://your-account-id.r2.cloudflarestorage.com"  # Replace with your R2 endpoint
CLOUDFLARE_R2_BUCKET = "sneaker-deals"  # Replace with your bucket name

# Dictionary mapping site names to their configuration
WEBSITES = {
    "sneakers": {
        "url": "https://www.sneakers.com",
        "sale_url": "https://www.sneakers.com/collections/sale",
    },
    "champssports": {
        "url": "https://www.champssports.com",
        "sale_url": "https://www.champssports.com/category/sale/shoes.html",
    },
    "footlocker": {
        "url": "https://www.footlocker.com",
        "sale_url": "https://www.footlocker.com/category/sale/shoes.html",
    },
    "idsports": {
        "url": "https://www.idsports.com",
        "sale_url": "https://www.idsports.com/sale",
    },
}

# Import extended site configurations from sites module
from config.sites import SNEAKER_SITES, DEFAULT_SITES, MARKET_PRICE_SITES
