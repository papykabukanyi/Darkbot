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

def run_scraper(scraper_instance, category='sale'):
    """
    Run a scraper for a specific site.
    
    Args:
        scraper_instance: Instance of a scraper
        category: Category to scrape (default: 'sale')
        
    Returns:
        List of deals found
    """
    deals = []
    
    try:
        logger.info(f"Scraping {scraper_instance.name}...")
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
            
            logger.info(f"Found {len(filtered_deals)} deals on {scraper_instance.name} meeting criteria")
            deals.extend(filtered_deals)
    
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
    
    all_deals = []
    
    # Initialize storage
    storage = DealStorage(
        csv_filename=CSV_FILENAME,
        db_enabled=DATABASE_ENABLED,
        db_path=DATABASE_PATH
    )    # Use mock data if in test mode
    if args.test_mode:
        try:
            from mock_data import load_mock_dataset
            all_deals = load_mock_dataset()
            logger.info(f"Test mode: Loaded {len(all_deals)} mock products")
            
            # Filter by brand if specified
            if args.brands:
                all_deals = [
                    deal for deal in all_deals
                    if deal.get('brand', '').lower() in [b.lower() for b in args.brands]
                ]
                
            # Filter by discount
            all_deals = [
                deal for deal in all_deals 
                if deal.get('discount_percent', 0) >= args.min_discount
            ]
            
            logger.info(f"Test mode: {len(all_deals)} products after filtering")
        except Exception as e:
            logger.error(f"Error loading mock data: {e}")
            return
    else:
        # Real scraping mode
        for site_name in tqdm(args.sites, desc="Scraping websites"):
            if site_name in WEBSITES:
                site_config = WEBSITES[site_name]
                
                try:
                    scraper_class = get_scraper_for_site(site_name, site_config)
                    with scraper_class as scraper:
                        site_deals = run_scraper(scraper)
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
        
        # Print deals to console
        if not args.quiet:
            print(f"\nFound {len(all_deals)} deals matching your criteria:")
            for deal in all_deals:
                print_deal(deal)
        
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
    
    else:
        print(f"\n{colorama.Fore.YELLOW}No deals found matching your criteria.{colorama.Style.RESET_ALL}")
    
    print(f"\nFinished at: {get_timestamp()}")

if __name__ == "__main__":
    main()
