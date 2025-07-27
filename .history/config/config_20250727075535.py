"""
Main configuration file for the Sneaker Bot.
"""

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
EMAIL_SERVER = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_ADDRESS = "your_email@gmail.com"  # Replace with your email
EMAIL_PASSWORD = "your_app_password"    # Replace with your app password
EMAIL_RECIPIENT = "your_email@gmail.com"  # Replace with recipient email

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
