"""
Package initialization for config.
"""

# Import and expose all configuration variables
from config.config import (
    WEBSITES, MIN_DISCOUNT_PERCENT, BRANDS_OF_INTEREST,
    SAVE_TO_CSV, CSV_FILENAME, DATABASE_ENABLED, DATABASE_PATH,
    EMAIL_NOTIFICATIONS, EMAIL_INTERVAL_MINUTES, EMAIL_SERVER,
    EMAIL_PORT, EMAIL_ADDRESS, EMAIL_PASSWORD, EMAIL_RECIPIENT
)

# Import site configurations
from config.sites import SNEAKER_SITES, DEFAULT_SITES, MARKET_PRICE_SITES
