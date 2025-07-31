"""
Improved main script for the Sneaker Bot - Full functionality with error handling.
"""

import argparse
import colorama
import datetime
import logging
import os
import random
import schedule
import sys
import time
from tqdm import tqdm

from config import (WEBSITES, MIN_DISCOUNT_PERCENT, BRANDS_OF_INTEREST,
                   SAVE_TO_CSV, CSV_FILENAME, DATABASE_ENABLED, DATABASE_PATH,
                   EMAIL_INTERVAL_MINUTES, EMAIL_NOTIFICATIONS,
                   MONGODB_ENABLED, MONGODB_CONNECTION_STRING, MONGODB_DATABASE, MONGODB_COLLECTION)

from scrapers.factory import get_scraper_for_site
from notifications import EmailNotifier
from storage import DealStorage
from utils.price_comparison import PriceComparer

# Set up logging with both file and console outputs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sneaker_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SneakerBot")

# Initialize colorama for colored terminal output
colorama.init()

def get_timestamp():
    """Get current timestamp for display."""
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def analyze_deals_for_profit(deals, price_comparer):
    """
    Analyze deals for profitability against market prices.
    
    Args:
        deals: List of deals to analyze
        price_comparer: PriceComparer instance with market data
        
    Returns:
        List of analyzed deals with profit information added
    """
    for deal in deals:
        # Calculate estimated market price (simple estimation for now)
        estimated_market_price = deal.get('original_price', 0) * 0.9  # 90% of MSRP as estimate
        
        # Calculate profit metrics
        if deal.get('price', 0) > 0 and estimated_market_price > 0:
            profit_amount = estimated_market_price - deal.get('price', 0)
            profit_percentage = (profit_amount / deal.get('price', 0)) * 100
            
            # Add profit data to the deal
            deal['profit_amount'] = round(profit_amount, 2)
            deal['profit_percentage'] = round(profit_percentage, 2)
            deal['is_profitable'] = profit_percentage >= 20  # 20% threshold
    
    return deals

def filter_deals(deals):
    """
    Filter deals based on criteria.
    
    Args:
        deals: List of deals to filter
        
    Returns:
        Filtered list of deals
    """
    if not deals:
        return []
    
    filtered_deals = []
    for deal in deals:
        # Filter by minimum discount
        if deal.get('discount_percent', 0) < MIN_DISCOUNT_PERCENT:
            continue
        
        # Filter by brands of interest
        if BRANDS_OF_INTEREST and deal.get('brand') and not any(
            brand.lower() in deal.get('brand', '').lower() for brand in BRANDS_OF_INTEREST
        ):
            continue
        
        filtered_deals.append(deal)
    
    return filtered_deals

def scrape_website(site_name, site_config):
    """
    Scrape a single website for deals.
    
    Args:
        site_name: Name of the site
        site_config: Configuration for the site
        
    Returns:
        List of deals found
    """
    logger.info(f"Starting scrape of {site_name}")
    
    try:
        # Get the appropriate scraper
        with get_scraper_for_site(site_name, site_config) as scraper:
            if not scraper:
                logger.error(f"Could not create scraper for {site_name}")
                return []
            
            # Start scraping
            deals = scraper.scrape_site()
            
            # Log results
            if deals:
                logger.info(f"Found {len(deals)} deals on {site_name}")
                return deals
            else:
                logger.warning(f"No deals found on {site_name}")
                return []
                
    except Exception as e:
        logger.error(f"Error scraping {site_name}: {e}")
        return []

def main(args):
    """Main function to run the bot."""
    # Print banner
    print("\n" + "="*50)
    print("\033[92m" + " 💰 SNEAKER DEAL FINDER BOT 👟 " + "\033[0m")
    print("="*50)
    print(f"Started at: {get_timestamp()}")
    print(f"Minimum discount: {MIN_DISCOUNT_PERCENT}%")
    print(f"Target brands: {', '.join(BRANDS_OF_INTEREST)}")
    print("="*50 + "\n")
    
    # Initialize storage
    logger.info("Initializing storage...")
    storage = DealStorage(
        csv_filename=CSV_FILENAME,
        db_enabled=DATABASE_ENABLED,
        db_path=DATABASE_PATH
    )
    
    # Initialize MongoDB storage if enabled
    mongodb_storage = None
    if MONGODB_ENABLED:
        try:
            # Try importing directly first
            try:
                from storage.mongodb import MongoDBStorage
            except ImportError:
                # Fall back to top-level storage module
                from storage import MongoDBStorage
                
            mongodb_storage = MongoDBStorage(
                connection_string=MONGODB_CONNECTION_STRING,
                database_name=MONGODB_DATABASE,
                collection_name=MONGODB_COLLECTION
            )
            logger.info("MongoDB storage initialized")
        except ImportError:
            logger.warning("MongoDB module not found. MongoDB storage disabled.")
        except Exception as e:
            logger.error(f"Error initializing MongoDB: {e}")
    
    # Initialize price comparer
    price_comparer = PriceComparer()
    
    # Initialize email notifier
    email_notifier = EmailNotifier() if EMAIL_NOTIFICATIONS else None
    if email_notifier and email_notifier.enabled:
        email_notifier.start_notification_thread()
    
    # Handle command-line args
    if args.sites:
        # Only scrape specific sites
        sites_to_scrape = {k: v for k, v in WEBSITES.items() if k in args.sites}
    else:
        # Scrape all sites
        sites_to_scrape = WEBSITES
    
    # Scrape each website
    all_deals = []
    
    print(f"Scraping {len(sites_to_scrape)} websites for deals...")
    for site_name, site_config in tqdm(sites_to_scrape.items(), desc="Sites scraped"):
        deals = scrape_website(site_name, site_config)
        if deals:
            all_deals.extend(deals)
        
        # Add random delay between sites
        if site_name != list(sites_to_scrape.keys())[-1]:  # Skip delay after last site
            delay = random.uniform(1.0, 3.0)
            time.sleep(delay)
    
    # Filter and analyze deals
    logger.info(f"Found {len(all_deals)} total deals before filtering")
    filtered_deals = filter_deals(all_deals)
    logger.info(f"Filtered to {len(filtered_deals)} deals that match criteria")
    
    # Analyze for profitability
    analyzed_deals = analyze_deals_for_profit(filtered_deals, price_comparer)
    
    # Sort deals by discount percentage (highest first)
    analyzed_deals.sort(key=lambda x: x.get('discount_percent', 0), reverse=True)
    
    # Save deals to storage
    if analyzed_deals:
        if SAVE_TO_CSV:
            storage.save_deals(analyzed_deals)
        
        if mongodb_storage:
            mongodb_storage.upload_deals(analyzed_deals)
        
        # Send email notification if enabled
        if email_notifier and email_notifier.enabled:
            email_notifier.send_deals_email(analyzed_deals)
    else:
        logger.info("No deals found that match the criteria")
        
        # Send "no deals" email notification if enabled
        if email_notifier and email_notifier.enabled:
            email_notifier.send_no_deals_notification()
    
    # Print summary
    print("\n" + "="*50)
    print(f"Summary: Found {len(analyzed_deals)} matching deals")
    print(f"Data saved to {CSV_FILENAME}" if SAVE_TO_CSV else "CSV saving disabled")
    print(f"Data saved to MongoDB" if mongodb_storage else "MongoDB saving disabled")
    print(f"Email notifications sent" if email_notifier and email_notifier.enabled else "Email notifications disabled")
    print("="*50)
    
    # Return deals for testing or further processing
    return analyzed_deals

def run_scheduled():
    """Run the bot on a schedule."""
    logger.info("Starting scheduled runs")
    
    # Parse empty args for scheduled run
    args = argparse.Namespace(sites=None, continuous=False)
    
    # Run once immediately
    main(args)
    
    # Schedule regular runs
    schedule.every(30).minutes.do(lambda: main(args))
    
    logger.info("Bot scheduled to run every 30 minutes")
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check schedule every minute

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Sneaker Deal Finder Bot')
    parser.add_argument('--sites', nargs='+', help='Specific sites to scrape')
    parser.add_argument('--continuous', action='store_true', help='Run continuously on a schedule')
    args = parser.parse_args()
    
    # Run the bot once or continuously
    if args.continuous:
        try:
            run_scheduled()
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            sys.exit(0)
    else:
        main(args)
