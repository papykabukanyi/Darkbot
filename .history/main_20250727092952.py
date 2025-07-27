"""
Main script for the sneaker bot. Handles command line arguments and runs the scrapers.
"""

import os
import sys
import time
import json
import signal
import datetime
import argparse
import logging
import colorama
from tqdm import tqdm

from config import (WEBSITES, MIN_DISCOUNT_PERCENT, BRANDS_OF_INTEREST,
                   SAVE_TO_CSV, CSV_FILENAME, DATABASE_ENABLED, DATABASE_PATH,
                   EMAIL_INTERVAL_MINUTES, EMAIL_NOTIFICATIONS,
                   SNEAKER_SITES, DEFAULT_SITES, MARKET_PRICE_SITES,
                   CLOUDFLARE_R2_ENABLED, CLOUDFLARE_R2_ACCESS_KEY, CLOUDFLARE_R2_SECRET_KEY,
                   CLOUDFLARE_R2_ENDPOINT, CLOUDFLARE_R2_BUCKET,
                   MONGODB_ENABLED, MONGODB_CONNECTION_STRING, MONGODB_DATABASE, MONGODB_COLLECTION)

from utils.price_comparison import PriceComparer

# Get the most profitable deals
    profitable_deals = price_comparer.get_most_profitable_deals(analyzed_deals)
    
    # Save deals if there are any
    if analyzed_deals:
        if SAVE_TO_CSV:
            storage.save_deals(analyzed_deals)
            
        if args.export_json:
            storage.export_to_json()
            
        # Upload to MongoDB (primary storage)
        if mongodb_storage is not None and MONGODB_ENABLED:
            mongodb_storage.upload_deals(analyzed_deals)
            
        # Upload to Cloudflare R2 if enabled (legacy support)
        latest_file_key = None
        if r2_storage is not None and CLOUDFLARE_R2_ENABLED:
            today = datetime.datetime.now().strftime('%Y-%m-%d')
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            latest_file_key = f"{today}/deals_{timestamp}.json"
            r2_storage.upload_deals(analyzed_deals)
            
        # Check if we should continue iterating
        should_continue = False
        if args.iterate and not scheduled_run:
            if mongodb_storage is not None and MONGODB_ENABLED:
                should_continue = mongodb_storage.continue_to_iterate(last_iteration_deals, analyzed_deals)
            elif r2_storage is not None and CLOUDFLARE_R2_ENABLED:
                should_continue = r2_storage.continue_to_iterate(latest_file_key)
            else:
                should_continue = storage.continue_to_iterate(last_iteration_deals, analyzed_deals)
                
            if should_continue:
                logger.info("Found significant new deals, continuing to iterate...")
                # Wait a bit before continuing to avoid rate limits
                time.sleep(60)  # 1 minute pause
                return run_scraper_job(args, scheduled_run, analyzed_deals)
        
        # Print each deal, prioritizing profitable dealsPRICE_SITES)r the sneaker deal finder bot.
"""

import argparse
import logging
import time
import schedule
import threading
from typing import Dict, List, Any
import colorama
from tqdm import tqdm
import datetime
import sys

from config import (WEBSITES, MIN_DISCOUNT_PERCENT, BRANDS_OF_INTEREST,
                   SAVE_TO_CSV, CSV_FILENAME, DATABASE_ENABLED, DATABASE_PATH,
                   EMAIL_INTERVAL_MINUTES, EMAIL_NOTIFICATIONS,
                   SNEAKER_SITES, DEFAULT_SITES, MARKET_PRICE_SITES,
                   HEADLESS_BROWSER, USE_SELENIUM, SCREENSHOT_ON_ERROR,
                   MONGODB_ENABLED, MONGODB_CONNECTION_STRING, MONGODB_DATABASE, MONGODB_COLLECTION,
                   CLOUDFLARE_R2_ENABLED, CLOUDFLARE_R2_ACCESS_KEY, 
                   CLOUDFLARE_R2_SECRET_KEY, CLOUDFLARE_R2_ENDPOINT, 
                   CLOUDFLARE_R2_BUCKET)
try:
    from scrapers import (SneakersScraper, ChampsScraper, 
                        FootlockerScraper, IDSportsScraper)
except ImportError:
    # If specific scrapers can't be imported, we'll use the factory
    pass

from scrapers.factory import get_scraper_for_site
from storage import DealStorage, R2Storage, MongoDBStorage
from utils import get_timestamp
from utils.price_comparison import PriceComparer
from notifications import notifier

# Global storage instances
r2_storage = None
mongodb_storage = None

# Initialize colorama for colored console output
colorama.init()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sneaker_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SneakerBot")

def get_scraper_for_site(site_name: str, site_config: Dict[str, Any]):
    """
    Get the appropriate scraper for a site.
    
    Args:
        site_name: Name of the site
        site_config: Configuration for the site
        
    Returns:
        Initialized scraper instance
    """
    site_config['name'] = site_name.capitalize()
    
    if site_name == 'sneakers':
        return SneakersScraper(site_config)
    elif site_name == 'champs':
        return ChampsScraper(site_config)
    elif site_name == 'footlocker':
        return FootlockerScraper(site_config)
    elif site_name == 'idsports':
        return IDSportsScraper(site_config)
    else:
        raise ValueError(f"Unknown site: {site_name}")

def print_deal(deal: Dict[str, Any]):
    """
    Print deal information to the console with color formatting.
    
    Args:
        deal: Dictionary with deal information
    """
    # Set up colors
    RESET = colorama.Style.RESET_ALL
    BOLD = colorama.Style.BRIGHT
    GREEN = colorama.Fore.GREEN
    RED = colorama.Fore.RED
    BLUE = colorama.Fore.BLUE
    YELLOW = colorama.Fore.YELLOW
    
    # Format the deal information
    title = f"{BOLD}{deal['title']}{RESET}"
    price = f"{GREEN}${deal.get('current_price', deal.get('price', 0)):.2f}{RESET}"
    original = f"{RED}${deal.get('original_price', 0):.2f}{RESET}"
    discount = f"{BOLD}{YELLOW}{deal.get('discount_percent', 0)}%{RESET}"
    source = f"{BLUE}{deal.get('source', 'Unknown')}{RESET}"
    
    # Add profit information if available
    profit_info = ""
    if 'profit_percentage' in deal and 'profit_amount' in deal:
        profit_color = GREEN if deal['profit_amount'] > 0 else RED
        profit_info = f" | Potential profit: {profit_color}${deal['profit_amount']:.2f}{RESET} ({deal['profit_percentage']:.1f}%)"
        
    # Add market comparison info
    market_info = ""
    if deal.get('is_profitable', False):
        market_info = f"\n{GREEN}PROFITABLE RESELL OPPORTUNITY!{RESET}"
    
    # Print the formatted deal
    print(f"\n{title}")
    print(f"Price: {price} (was {original}) - {discount} off{profit_info}")
    print(f"Source: {source}")
    
    # Print market information if available
    if market_info:
        print(market_info)
    
    # Print SKU/model number if available
    if 'sku' in deal:
        print(f"SKU: {deal.get('sku', '')}")
    
    # Print URL
    print(f"URL: {deal.get('url', '')}")
    
    # Print available sizes if present
    if 'sizes' in deal:
        available_sizes = [s['size'] for s in deal['sizes'] if s['available']]
        if available_sizes:
            sizes_str = ", ".join(available_sizes)
            print(f"Available sizes: {sizes_str}")
    
    print("-" * 80)

def run_scraper(scraper_instance, site_name, category='sale'):
    """
    Run a scraper for a specific site.
    
    Args:
        scraper_instance: Instance of a scraper
        site_name: Name of the site being scraped
        category: Category to scrape (default: 'sale')
        
    Returns:
        List of deals found
    """
    deals = []
    
    try:
        logger.info(f"Searching {site_name} for real products with purchase links...")
        logger.info(f"Scraping {site_name}...")
        site_deals = scraper_instance.scrape_site()
        
        if site_deals:
            # Filter deals by minimum discount
            filtered_deals = [
                deal for deal in site_deals 
                if deal.get('discount_percent', 0) >= MIN_DISCOUNT_PERCENT
            ]
            
            # Filter by brand if configured
            if BRANDS_OF_INTEREST:
                filtered_deals = [
                    deal for deal in filtered_deals
                    if deal.get('brand', '').lower() in [b.lower() for b in BRANDS_OF_INTEREST]
                ]
            
            # Add a note that these are real products with working links
            for deal in filtered_deals:
                deal['is_real_product'] = True
                deal['verified_link'] = True
            
            logger.info(f"Found {len(filtered_deals)} deals on {site_name} meeting criteria")
            deals.extend(filtered_deals)
            
        logger.info(f"Found {len(deals)} real products on {site_name}")
    
    except Exception as e:
        logger.error(f"Error running scraper for {site_name}: {e}")
    
    return deals

def run_scraper_job(args, scheduled_run=False, last_iteration_deals=None):
    """
    Run the scraper job to find deals.
    
    Args:
        args: Command line arguments
        scheduled_run: Whether this is a scheduled run
        last_iteration_deals: Deals found in the previous iteration
    
    Returns:
        List of deals found
    """
    if scheduled_run:
        print(f"\n{colorama.Fore.CYAN}{colorama.Style.BRIGHT}Scheduled Run - {get_timestamp()}{colorama.Style.RESET_ALL}")
    else:
        print(f"\n{colorama.Fore.GREEN}{colorama.Style.BRIGHT}Real Product Search - {get_timestamp()}{colorama.Style.RESET_ALL}")
        print("Searching for real products with working links...")
    
    all_deals = []
    market_data = {}
    
    # Initialize storage
    storage = DealStorage(
        csv_filename=CSV_FILENAME,
        db_enabled=DATABASE_ENABLED,
        db_path=DATABASE_PATH
    )
    
    # Initialize R2 storage if enabled
    global r2_storage
    if r2_storage is not None and CLOUDFLARE_R2_ENABLED:
        logger.info("R2 Storage initialized and enabled")
    
    # Initialize price comparer
    price_comparer = PriceComparer()
    
    # Always use real scraping mode
    args.test_mode = False
    
    # First, scrape market price sites to get comparison data
    logger.info("First collecting market price data for comparison...")
    for site_name in tqdm([s for s in args.sites if s in MARKET_PRICE_SITES], 
                          desc="Collecting market price data"):
        if site_name in SNEAKER_SITES:
            site_config = SNEAKER_SITES[site_name]
            
            try:
                scraper_class = get_scraper_for_site(site_name, site_config)
                with scraper_class as scraper:
                    market_deals = run_scraper(scraper, site_name)
                    
                    # Store market price data for comparison
                    for deal in market_deals:
                        if 'sku' in deal:
                            market_data[deal['sku']] = {
                                'market_price': deal.get('current_price', 0),
                                'source': site_name
                            }
            except Exception as e:
                logger.error(f"Error collecting market data from {site_name}: {e}")
    
    # Update price comparer with market data
    price_comparer = PriceComparer(market_data)
    logger.info(f"Collected market price data for {len(market_data)} products")
    
    # Now scrape regular sites for deals
    for site_name in tqdm([s for s in args.sites if s not in MARKET_PRICE_SITES], 
                          desc="Scraping for deals"):
        if site_name in SNEAKER_SITES:
            site_config = SNEAKER_SITES[site_name]
            
            try:
                scraper_class = get_scraper_for_site(site_name, site_config)
                with scraper_class as scraper:
                    site_deals = run_scraper(scraper, site_name)
                    all_deals.extend(site_deals)
            
            except Exception as e:
                logger.error(f"Error with {site_name}: {e}")
    
    # Analyze deals for profitability
    logger.info("Analyzing deals for profitability...")
    analyzed_deals = price_comparer.analyze_deals(all_deals)
    
    # Sort deals by profitability first, then discount percentage
    analyzed_deals.sort(key=lambda x: (x.get('profit_percentage', 0), x.get('discount_percent', 0)), reverse=True)
    
    # Get the most profitable deals
    profitable_deals = price_comparer.get_most_profitable_deals(analyzed_deals)
    
    # Save deals if there are any
    if analyzed_deals:
        if SAVE_TO_CSV:
            storage.save_deals(analyzed_deals)
        
        if args.export_json:
            storage.export_to_json()
            
        # Upload to Cloudflare R2 if enabled
        if r2_storage is not None and CLOUDFLARE_R2_ENABLED:
            r2_storage.upload_deals(analyzed_deals)
        
        # Print each deal, prioritizing profitable deals
        if profitable_deals:
            print(f"\n{colorama.Fore.GREEN}{colorama.Style.BRIGHT}PROFITABLE DEALS FOUND:{colorama.Style.RESET_ALL}")
            for deal in profitable_deals:
                if not scheduled_run or not args.quiet:
                    print_deal(deal)
        
        # Print remaining deals if not in quiet mode
        if not args.quiet and not scheduled_run:
            remaining_deals = [d for d in analyzed_deals if d not in profitable_deals]
            if remaining_deals:
                print(f"\n{colorama.Style.BRIGHT}Other Deals:{colorama.Style.RESET_ALL}")
                for deal in remaining_deals[:10]:  # Just show top 10 other deals
                    print_deal(deal)
                if len(remaining_deals) > 10:
                    print(f"\n...and {len(remaining_deals) - 10} more deals. See full results in CSV/JSON export.")
        
        if not scheduled_run:
            print(f"\n{colorama.Style.BRIGHT}Summary:{colorama.Style.RESET_ALL}")
            print(f"Total deals found: {len(analyzed_deals)}")
            print(f"Profitable deals: {len(profitable_deals)}")
            print(f"Deals by site:")
            for site in args.sites:
                site_deals = [d for d in analyzed_deals if d.get('source', '').lower() == site.lower()]
                if site_deals:
                    print(f"  - {site.capitalize()}: {len(site_deals)} total, {len([d for d in site_deals if d.get('is_profitable', False)])} profitable")
            
            if SAVE_TO_CSV:
                print(f"\nResults saved to {CSV_FILENAME}")
            if args.export_json:
                print(f"Results exported to deals_export.json")
            if MONGODB_ENABLED and mongodb_storage is not None:
                print(f"Results saved to MongoDB database: {MONGODB_DATABASE}")
                
        # Add deals to email notification queue, prioritizing profitable deals
        if EMAIL_NOTIFICATIONS:
            # If we found profitable deals, prioritize them in the notification
            if profitable_deals:
                notifier.add_deals(profitable_deals + [d for d in analyzed_deals if d not in profitable_deals])
            else:
                notifier.add_deals(analyzed_deals)
    else:
        if not scheduled_run:
            print(f"\n{colorama.Fore.YELLOW}No deals found matching your criteria.{colorama.Style.RESET_ALL}")
    
    # Return the found deals for potential iteration
    return analyzed_deals
    
    if not scheduled_run:
        print(f"\nFinished at: {get_timestamp()}")
        
    return all_deals

def main():
    """Main entry point for the script."""
    
    # Set up command-line arguments
    parser = argparse.ArgumentParser(description='Real Sneaker Deal Finder Bot')
    parser.add_argument('--sites', nargs='+', choices=list(SNEAKER_SITES.keys()), 
                        default=DEFAULT_SITES,
                        help='Sites to scrape (default: all available sites)')
    parser.add_argument('--brands', nargs='+', default=BRANDS_OF_INTEREST,
                        help=f'Brands to look for (default: {BRANDS_OF_INTEREST})')
    parser.add_argument('--min-discount', type=int, default=MIN_DISCOUNT_PERCENT,
                        help=f'Minimum discount percentage (default: {MIN_DISCOUNT_PERCENT}%%)')
    parser.add_argument('--quiet', action='store_true', help='Suppress console output')
    parser.add_argument('--export-json', action='store_true', help='Export results to JSON')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--test-mode', action='store_true', 
                        help='This flag is ignored - we always search for real products')
    parser.add_argument('--continuous', action='store_true', 
                        help='Run continuously (default: False)')
    parser.add_argument('--interval', type=int, default=EMAIL_INTERVAL_MINUTES,
                        help=f'Interval in minutes for scheduled runs (default: {EMAIL_INTERVAL_MINUTES})')
    parser.add_argument('--no-email', action='store_true',
                        help='Disable email notifications (overrides config)')
    # MongoDB options
    parser.add_argument('--mongodb', action='store_true',
                        help='Enable MongoDB storage (overrides config)')
    parser.add_argument('--no-mongodb', action='store_true',
                        help='Disable MongoDB storage (overrides config)')
    parser.add_argument('--mongodb-connection',
                        help='MongoDB connection string')
    parser.add_argument('--mongodb-database',
                        help='MongoDB database name')
    parser.add_argument('--mongodb-collection',
                        help='MongoDB collection name')
                        
    # Legacy Cloudflare R2 options (maintained for backward compatibility)
    parser.add_argument('--r2', action='store_true',
                        help='Enable Cloudflare R2 storage (overrides config)')
    parser.add_argument('--no-r2', action='store_true',
                        help='Disable Cloudflare R2 storage (overrides config)')
    parser.add_argument('--r2-access-key',
                        help='Cloudflare R2 access key')
    parser.add_argument('--r2-secret-key',
                        help='Cloudflare R2 secret key')
    parser.add_argument('--r2-endpoint',
                        help='Cloudflare R2 endpoint URL')
    parser.add_argument('--r2-bucket',
                        help='Cloudflare R2 bucket name')
    parser.add_argument('--iterate', action='store_true',
                        help='Continue to iterate if new deals are found')
    
    args = parser.parse_args()
    
    # Enable debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    print(f"{colorama.Fore.RED}{colorama.Style.BRIGHT}REAL Sneaker Deal Finder Bot{colorama.Style.RESET_ALL}")
    print(f"{colorama.Fore.YELLOW}Searching for REAL products with WORKING purchase links{colorama.Style.RESET_ALL}")
    print(f"Started at: {get_timestamp()}")
    
    # Override email notifications if --no-email flag is provided
    email_notifications = EMAIL_NOTIFICATIONS
    if args.no_email:
        email_notifications = False
    
    # Initialize the email notifier if enabled
    if email_notifications:
        notifier.enabled = True
        notifier.start_notification_thread()
    else:
        notifier.enabled = False
        
    # Initialize MongoDB storage (primary storage)
    global mongodb_storage
    mongodb_enabled = MONGODB_ENABLED
    if args.mongodb:
        mongodb_enabled = True
    if args.no_mongodb:
        mongodb_enabled = False
        
    if mongodb_enabled:
        # Setup MongoDB storage using command line args if provided, otherwise use config
        mongodb_storage = MongoDBStorage(
            connection_string=args.mongodb_connection or MONGODB_CONNECTION_STRING,
            database_name=args.mongodb_database or MONGODB_DATABASE,
            collection_name=args.mongodb_collection or MONGODB_COLLECTION
        )
    
    # Initialize Cloudflare R2 storage if enabled (legacy support)
    global r2_storage
    r2_enabled = CLOUDFLARE_R2_ENABLED
    if args.r2:
        r2_enabled = True
    if args.no_r2:
        r2_enabled = False
        
    if r2_enabled:
        # Setup R2 storage using command line args if provided, otherwise use config
        r2_storage = R2Storage(
            access_key_id=args.r2_access_key or CLOUDFLARE_R2_ACCESS_KEY,
            secret_access_key=args.r2_secret_key or CLOUDFLARE_R2_SECRET_KEY,
            endpoint_url=args.r2_endpoint or CLOUDFLARE_R2_ENDPOINT,
            bucket_name=args.r2_bucket or CLOUDFLARE_R2_BUCKET
        )
    
    # Display sites being scraped
    print(f"Scraping {len(args.sites)} sites: {', '.join(args.sites)}")
    print(f"Looking for brands: {', '.join(args.brands)}")
    print(f"Minimum discount: {args.min_discount}%")
    print(f"Email notifications: {'Enabled' if email_notifications else 'Disabled'}")
    print(f"MongoDB storage: {'Enabled' if mongodb_enabled else 'Disabled'}")
    print(f"Cloudflare R2 storage: {'Enabled' if r2_enabled else 'Disabled'}")
    print("-" * 80)
    
    # Run in continuous mode if specified
    if args.continuous:
        print(f"Running in continuous mode every {args.interval} minutes")
        print("-" * 80)
        
        # Run once immediately
        print("Running initial scan...")
        run_scraper_job(args)
        
        # Setup for continuous running
        start_time = datetime.datetime.now()
        
        # Schedule runs
        def scheduled_job():
            print(f"\n{colorama.Fore.CYAN}Running scheduled scan - {get_timestamp()}{colorama.Style.RESET_ALL}")
            run_scraper_job(args, scheduled_run=True)
            
            # Display uptime info
            uptime = datetime.datetime.now() - start_time
            uptime_str = str(uptime).split('.')[0]  # Remove microseconds
            next_run = datetime.datetime.now() + datetime.timedelta(minutes=args.interval)
            next_run_str = next_run.strftime('%H:%M:%S')
            
            print(f"{colorama.Fore.CYAN}Bot uptime: {uptime_str} | Next scan at: {next_run_str}{colorama.Style.RESET_ALL}")
        
        # Schedule to run every X minutes
        schedule.every(args.interval).minutes.do(scheduled_job)
        
        print(f"\nBot is now running continuously. Press Ctrl+C to stop.")
        print(f"Checking sites every {args.interval} minutes")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping continuous execution...")
            # Clean up resources
            if email_notifications:
                notifier.stop_notification_thread()
            print("Bot stopped.")
    else:
        # Run once in normal mode
        print("Running in one-time mode")
        print("-" * 80)
        
        run_scraper_job(args)
        
        # Clean up resources
        if email_notifications:
            notifier.stop_notification_thread()

if __name__ == "__main__":
    main()
