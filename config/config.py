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

# MongoDB settings
MONGODB_ENABLED = True  # Set to True to enable MongoDB storage
MONGODB_CONNECTION_STRING = "mongodb://mongo:SMhYDmJOIDZMrHqHhVJRIHzxcOfJUaNr@shortline.proxy.rlwy.net:51019"
MONGODB_DATABASE = "sneaker_deals"
MONGODB_COLLECTION = "deals"

# Cloudflare R2 settings (Legacy - replaced by MongoDB)
CLOUDFLARE_R2_ENABLED = False  # Set to True to enable R2 storage
CLOUDFLARE_R2_ACCESS_KEY = ""  # Your Cloudflare R2 access key
CLOUDFLARE_R2_SECRET_KEY = ""  # Your Cloudflare R2 secret key
CLOUDFLARE_R2_ENDPOINT = ""    # Your Cloudflare R2 endpoint URL
CLOUDFLARE_R2_BUCKET = "sneaker-deals"  # Your Cloudflare R2 bucket name

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
