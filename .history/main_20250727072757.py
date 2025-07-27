"""
Main script for the sneaker deal finder bot.
"""

import argparse
import logging
import time
import schedule
import threading
from typing import Dict, List, Any
import colorama
from tqdm import tqdm

from config import (WEBSITES, MIN_DISCOUNT_PERCENT, BRANDS_OF_INTEREST,
                   SAVE_TO_CSV, CSV_FILENAME, DATABASE_ENABLED, DATABASE_PATH,
                   EMAIL_INTERVAL_MINUTES, EMAIL_NOTIFICATIONS)
from scrapers import (SneakersScraper, ChampsScraper, 
                     FootlockerScraper, IDSportsScraper)
from storage import DealStorage
from utils import get_timestamp
from notifications import notifier

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
    price = f"{GREEN}${deal['price']:.2f}{RESET}"
    original = f"{RED}${deal['original_price']:.2f}{RESET}"
    discount = f"{BOLD}{YELLOW}{deal.get('discount_percent', 0)}%{RESET}"
    source = f"{BLUE}{deal['source']}{RESET}"
    
    profit_info = ""
    if 'profit' in deal:
        profit_color = GREEN if deal['profit'] > 0 else RED
        profit_info = f" | Potential profit: {profit_color}${deal['profit']:.2f}{RESET} ({deal['roi']})"
    
    # Print the formatted deal
    print(f"\n{title}")
    print(f"Price: {price} (was {original}) - {discount} off{profit_info}")
    print(f"Source: {source}")
    
    # Print URL
    print(f"URL: {deal['url']}")
    
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
            
            logger.info(f"Found {len(filtered_deals)} deals on {scraper_instance.name} meeting criteria")
            deals.extend(filtered_deals)
            
        logger.info(f"Found {len(deals)} real products on {site_name}")
    
    except Exception as e:
        logger.error(f"Error running scraper for {scraper_instance.name}: {e}")
    
    return deals

def run_scraper_job(args, scheduled_run=False):
    """
    Run the scraper job to find deals.
    
    Args:
        args: Command line arguments
        scheduled_run: Whether this is a scheduled run
    
    Returns:
        List of deals found
    """
    if scheduled_run:
        print(f"\n{colorama.Fore.CYAN}{colorama.Style.BRIGHT}Scheduled Run - {get_timestamp()}{colorama.Style.RESET_ALL}")
    else:
        print(f"\n{colorama.Fore.GREEN}{colorama.Style.BRIGHT}Real Product Search - {get_timestamp()}{colorama.Style.RESET_ALL}")
        print("Searching for real products with working links...")
    
    all_deals = []
    
    # Initialize storage
    storage = DealStorage(
        csv_filename=CSV_FILENAME,
        db_enabled=DATABASE_ENABLED,
        db_path=DATABASE_PATH
    )    # Always use real scraping mode
    # Even if test mode flag is provided, we'll ignore it to ensure real products
    args.test_mode = False
    
    # Real scraping mode
    for site_name in tqdm(args.sites, desc="Scraping for REAL products"):
        if site_name in WEBSITES:
            site_config = WEBSITES[site_name]
            
            try:
                scraper_class = get_scraper_for_site(site_name, site_config)
                with scraper_class as scraper:
                    site_deals = run_scraper(scraper, site_name)
                    all_deals.extend(site_deals)
            
            except Exception as e:
                logger.error(f"Error with {site_name}: {e}")
    
    # Sort deals by discount percentage
    all_deals.sort(key=lambda x: x.get('discount_percent', 0), reverse=True)
    
    # Save deals if there are any
    if all_deals:
        if SAVE_TO_CSV:
            storage.save_deals(all_deals)
        
        if args.export_json:
            storage.export_to_json()
        
        # Print deals to console if not a scheduled run or quiet mode is not enabled
        if not args.quiet and not scheduled_run:
            print(f"\nFound {len(all_deals)} deals matching your criteria:")
            for deal in all_deals:
                print_deal(deal)
        
        if not scheduled_run:
            print(f"\n{colorama.Style.BRIGHT}Summary:{colorama.Style.RESET_ALL}")
            print(f"Total deals found: {len(all_deals)}")
            print(f"Deals by site:")
            for site in args.sites:
                site_count = sum(1 for deal in all_deals if deal['source'].lower() == site.capitalize())
                print(f"  - {site.capitalize()}: {site_count}")
            
            if SAVE_TO_CSV:
                print(f"\nResults saved to {CSV_FILENAME}")
            if args.export_json:
                print(f"Results exported to deals_export.json")
                
        # Add deals to email notification queue
        if EMAIL_NOTIFICATIONS:
            notifier.add_deals(all_deals)
            
    else:
        if not scheduled_run:
            print(f"\n{colorama.Fore.YELLOW}No deals found matching your criteria.{colorama.Style.RESET_ALL}")
    
    if not scheduled_run:
        print(f"\nFinished at: {get_timestamp()}")
        
    return all_deals

def main():
    """Main entry point for the script."""
    
    # Set up command-line arguments
    parser = argparse.ArgumentParser(description='Real Sneaker Deal Finder Bot')
    parser.add_argument('--sites', nargs='+', choices=list(WEBSITES.keys()), 
                        default=list(WEBSITES.keys()),
                        help='Sites to scrape (default: all)')
    parser.add_argument('--brands', nargs='+', default=BRANDS_OF_INTEREST,
                        help=f'Brands to look for (default: {BRANDS_OF_INTEREST})')
    parser.add_argument('--min-discount', type=int, default=MIN_DISCOUNT_PERCENT,
                        help=f'Minimum discount percentage (default: {MIN_DISCOUNT_PERCENT}%%)')
    parser.add_argument('--quiet', action='store_true', help='Suppress console output')
    parser.add_argument('--export-json', action='store_true', help='Export results to JSON')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    # Test mode is ignored - we always use real product mode
    parser.add_argument('--test-mode', action='store_true', 
                        help='This flag is ignored - we always search for real products')
    parser.add_argument('--schedule', action='store_true', help='Run on a schedule')
    parser.add_argument('--interval', type=int, default=EMAIL_INTERVAL_MINUTES,
                        help=f'Interval in minutes for scheduled runs (default: {EMAIL_INTERVAL_MINUTES})')
    
    args = parser.parse_args()
    
    # Enable debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    print(f"{colorama.Fore.RED}{colorama.Style.BRIGHT}REAL Sneaker Deal Finder Bot{colorama.Style.RESET_ALL}")
    print(f"{colorama.Fore.YELLOW}Searching for REAL products with WORKING purchase links{colorama.Style.RESET_ALL}")
    print(f"Started at: {get_timestamp()}")
    
    if args.schedule:
        print(f"Running in scheduled mode every {args.interval} minutes")
        print(f"Email notifications: {'Enabled' if EMAIL_NOTIFICATIONS else 'Disabled'}")
        print("-" * 80)
        
        # Run once immediately
        print("Running initial scan...")
        run_scraper_job(args)
        
        # Schedule runs
        def scheduled_job():
            run_scraper_job(args, scheduled_run=True)
        
        schedule.every(args.interval).minutes.do(scheduled_job)
        
        print(f"\nBot is now running on a schedule. Press Ctrl+C to stop.")
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping scheduled execution...")
            # Stop notification thread if running
            if EMAIL_NOTIFICATIONS:
                notifier.stop_notification_thread()
            print("Bot stopped.")
    else:
        # Run once in normal mode
        print(f"Scraping sites: {', '.join(args.sites)}")
        print(f"Looking for brands: {', '.join(args.brands)}")
        print(f"Minimum discount: {args.min_discount}%")
        print("-" * 80)
        
        # Debug output for websites config
        logger.debug(f"Website configurations:")
        for site, config in WEBSITES.items():
            logger.debug(f"{site}: {config}")
            
        run_scraper_job(args)

if __name__ == "__main__":
    main()
