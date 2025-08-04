@echo off
REM Darkbot Fix Script - Fixes R2Storage import errors

echo === Darkbot Fix Script ===
echo This script will fix the R2Storage import errors
echo by removing all R2Storage references

echo.
echo [1/3] Creating backup of main.py...
if exist main.py.bak (
    echo Backup already exists, skipping backup
) else (
    copy main.py main.py.bak
    echo Backup created: main.py.bak
)

echo.
echo [2/3] Renaming original main.py to main_original.py...
if exist main_original.py (
    echo main_original.py already exists, skipping rename
) else (
    copy main.py main_original.py
    echo Copied to main_original.py
)

echo.
echo [3/3] Creating fixed main.py...
echo """
echo Main script for the Sneaker Bot - MongoDB optimized version.
echo Fixed version that removes R2Storage references.
echo """
echo.
echo import argparse
echo import colorama
echo import datetime
echo import logging
echo import random
echo import schedule
echo import time
echo import sys
echo from tqdm import tqdm
echo.
echo from config import (WEBSITES, MIN_DISCOUNT_PERCENT, BRANDS_OF_INTEREST,
echo                   SAVE_TO_CSV, CSV_FILENAME, DATABASE_ENABLED, DATABASE_PATH,
echo                   EMAIL_INTERVAL_MINUTES, EMAIL_NOTIFICATIONS,
echo                   SNEAKER_SITES, DEFAULT_SITES, MARKET_PRICE_SITES,
echo                   MONGODB_ENABLED, MONGODB_CONNECTION_STRING, MONGODB_DATABASE, MONGODB_COLLECTION^)
echo.
echo from scrapers.factory import get_scraper_for_site
echo from notifications import EmailNotifier
echo from storage import DealStorage, MongoDBStorage
echo from utils.price_comparison import PriceComparer
echo.
echo # Set up logging
echo logging.basicConfig(
echo     level=logging.INFO,
echo     format='%%%(asctime)s - %%%(name)s - %%%(levelname)s - %%%(message)s'
echo ^)
echo logger = logging.getLogger("SneakerBot"^)
echo.
echo # Initialize colorama for colored output
echo colorama.init(^)
echo.
echo # Global storage instances
echo mongodb_storage = None
echo.
echo def get_timestamp(^):
echo     """Get current timestamp for display."""
echo     return datetime.datetime.now(^).strftime('%%Y-%%m-%%d %%H:%%M:%%S'^)
echo.
echo # Import the original functions but don't use R2Storage
echo try:
echo     # Import everything except main function from original file
echo     from main_original import analyze_deals_for_profit, save_and_upload_deals, run_scraper, run_scraper_job
echo     
echo     # Define a new main function that doesn't use R2Storage
echo     def main(^):
echo         """Main function."""
echo         parser = argparse.ArgumentParser(description='Sneaker Deal Bot - MongoDB Optimized'^)
echo         
echo         # Site selection
echo         parser.add_argument('--sites', nargs='+', default=DEFAULT_SITES,
echo                             help='Sites to scrape (default: recommended sites'^)
echo         parser.add_argument('--list-sites', action='store_true',
echo                             help='List available sites and exit'^)
echo         
echo         # Running mode
echo         parser.add_argument('--continuous', action='store_true',
echo                             help='Run continuously'^)
echo         parser.add_argument('--interval', type=int, default=60,
echo                             help='Interval between runs in seconds (default: 60'^)
echo         parser.add_argument('--report-interval', type=int, default=1800,
echo                             help='Email report interval in seconds (default: 1800 - 30 minutes'^)
echo         parser.add_argument('--iterate', action='store_true',
echo                             help='Keep scraping until no new deals are found'^)
echo         parser.add_argument('--max-iterations', type=int, default=5,
echo                             help='Maximum number of iterations when using --iterate'^)
echo         
echo         # Output options
echo         parser.add_argument('--verbose', action='store_true',
echo                             help='Enable verbose output'^)
echo         parser.add_argument('--export-json', action='store_true',
echo                             help='Export deals to JSON'^)
echo         parser.add_argument('--verify-sites', action='store_true',
echo                             help='Verify site availability before scraping'^)
echo         
echo         # Email options
echo         parser.add_argument('--email', action='store_true',
echo                             help='Enable email notifications (overrides config'^)
echo         parser.add_argument('--no-email', action='store_true',
echo                             help='Disable email notifications'^)
echo         
echo         # Storage options
echo         parser.add_argument('--csv', action='store_true',
echo                             help='Enable CSV storage (overrides config'^)
echo         parser.add_argument('--no-csv', action='store_true',
echo                             help='Disable CSV storage'^)
echo         
echo         # MongoDB options
echo         parser.add_argument('--mongodb', action='store_true',
echo                             help='Enable MongoDB storage (overrides config'^)
echo         parser.add_argument('--no-mongodb', action='store_true',
echo                             help='Disable MongoDB storage'^)
echo         parser.add_argument('--mongodb-connection', help='MongoDB connection string'^)
echo         parser.add_argument('--mongodb-database', help='MongoDB database name'^)
echo         parser.add_argument('--mongodb-collection', help='MongoDB collection name'^)
echo         
echo         args = parser.parse_args(^)
echo         
echo         # Run the original code with our args, but without R2Storage
echo         run_scraper_job(args^)
echo             
echo except ImportError as e:
echo     print(f"Error importing from main_original: {e}")
echo     print("Please ensure main_original.py exists and has the required functions.")
echo     sys.exit(1)
echo.
echo if __name__ == "__main__":
echo     try:
echo         main(^)
echo     except KeyboardInterrupt:
echo         print(f"\n{colorama.Fore.RED}Interrupted by user. Exiting...{colorama.Style.RESET_ALL}")
echo         sys.exit(0)
> main.py.new

move /Y main.py.new main.py

echo.
echo === Fix Complete ===
echo The R2Storage references have been removed.
echo Main changes:
echo  - Original main.py backed up to main.py.bak
echo  - Original main.py copied to main_original.py for reference
echo  - New main.py created without R2Storage references
echo.
echo You can now deploy this version to Railway.

pause
